from typing import Any

from ..models import ActionLog, LogResult
from .base import BasePlatform


class MockPlatform(BasePlatform):
    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.entries: list[ActionLog] = []
        self._fail: bool = False

    def set_fail(self, fail: bool = True):
        self._fail = fail

    def _emit(self, entry: ActionLog) -> LogResult:
        if self._fail:
            raise RuntimeError("mock platform forced failure")
        self.entries.append(entry)
        return LogResult(success=True, platform=self.name, action_id=entry.id)

    def clear(self):
        self.entries.clear()
