import abc
import time
from collections.abc import Callable
from typing import Any

from ..models import ActionLog, LogResult, PlatformHealth


class BasePlatform(abc.ABC):
    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self._enabled = self.config.get("enabled", True)
        self._failure_count = 0
        self._circuit_open_until: float = 0.0
        self._last_success: float | None = None
        self._last_failure: float | None = None
        self._queue: list[ActionLog] = []
        self._circuit_threshold = self.config.get("circuit_breaker", {}).get("threshold", 5)
        self._circuit_recovery = self.config.get("circuit_breaker", {}).get("recovery_time", 30.0)
        self._max_retries = self.config.get("retry", {}).get("max_attempts", 3)
        self._backoff = self.config.get("retry", {}).get("backoff", [0.5, 1.5, 4.5])
        self._max_queue = self.config.get("buffering", {}).get("max_size", 1000)
        self._flush_interval = self.config.get("buffering", {}).get("flush_interval", 5.0)
        self._last_flush = time.time()

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def name(self) -> str:
        return type(self).__name__.replace("Platform", "").lower()

    @abc.abstractmethod
    def _emit(self, entry: ActionLog) -> LogResult:
        ...

    def _emit_async(self, entry: ActionLog) -> LogResult:
        return self._emit(entry)

    def emit(self, entry: ActionLog) -> LogResult:
        if not self._enabled:
            return LogResult(success=True, platform=self.name, action_id=entry.id)

        if self._circuit_open():
            self._enqueue(entry)
            return LogResult(
                success=False,
                platform=self.name,
                action_id=entry.id,
                error="circuit_breaker_open",
            )

        for attempt in range(self._max_retries):
            try:
                t0 = time.time()
                result = self._emit(entry)
                duration = (time.time() - t0) * 1000
                result.duration_ms = duration
                self._last_success = time.time()
                self._failure_count = 0
                self._flush_queue()
                return result
            except Exception as e:
                self._failure_count += 1
                self._last_failure = time.time()
                if attempt < self._max_retries - 1:
                    delay = self._backoff[min(attempt, len(self._backoff) - 1)]
                    time.sleep(delay)
                else:
                    if self._failure_count >= self._circuit_threshold:
                        self._circuit_open_until = time.time() + self._circuit_recovery
                    self._enqueue(entry)
                    return LogResult(
                        success=False,
                        platform=self.name,
                        action_id=entry.id,
                        error=str(e),
                    )
        return LogResult(success=False, platform=self.name, action_id=entry.id, error="max_retries")

    async def aemit(self, entry: ActionLog) -> LogResult:
        if not self._enabled:
            return LogResult(success=True, platform=self.name, action_id=entry.id)

        if self._circuit_open():
            self._enqueue(entry)
            return LogResult(
                success=False,
                platform=self.name,
                action_id=entry.id,
                error="circuit_breaker_open",
            )

        for attempt in range(self._max_retries):
            try:
                t0 = time.time()
                result = await self._aemit(entry)
                duration = (time.time() - t0) * 1000
                result.duration_ms = duration
                self._last_success = time.time()
                self._failure_count = 0
                self._flush_queue()
                return result
            except Exception as e:
                self._failure_count += 1
                self._last_failure = time.time()
                if attempt < self._max_retries - 1:
                    delay = self._backoff[min(attempt, len(self._backoff) - 1)]
                    time.sleep(delay)
                else:
                    if self._failure_count >= self._circuit_threshold:
                        self._circuit_open_until = time.time() + self._circuit_recovery
                    self._enqueue(entry)
                    return LogResult(
                        success=False,
                        platform=self.name,
                        action_id=entry.id,
                        error=str(e),
                    )
        return LogResult(success=False, platform=self.name, action_id=entry.id, error="max_retries")

    async def _aemit(self, entry: ActionLog) -> LogResult:
        return self._emit(entry)

    def _circuit_open(self) -> bool:
        if self._failure_count < self._circuit_threshold:
            return False
        if time.time() < self._circuit_open_until:
            return True
        self._failure_count = 0
        return False

    def _enqueue(self, entry: ActionLog):
        if len(self._queue) < self._max_queue:
            self._queue.append(entry)

    def _flush_queue(self):
        self._queue.clear()
        self._last_flush = time.time()

    def flush(self):
        while self._queue:
            entry = self._queue.pop(0)
            self._emit(entry)
        self._last_flush = time.time()

    def health(self) -> PlatformHealth:
        status = "ok"
        error = None
        if self._circuit_open():
            status = "down"
            error = "circuit_breaker_open"
        elif self._failure_count > 0:
            status = "degraded"
        return PlatformHealth(
            platform=self.name,
            status=status,
            error=error,
            queue_size=len(self._queue),
            last_success=__import__("datetime").datetime.fromtimestamp(self._last_success)
            if self._last_success else None,
            last_failure=__import__("datetime").datetime.fromtimestamp(self._last_failure)
            if self._last_failure else None,
        )
