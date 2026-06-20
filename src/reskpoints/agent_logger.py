import os
import platform
import random
import time
from pathlib import Path
from typing import Any

from .config import AgentLoggerConfig
from .masking import FieldMasker
from .models import ActionLog, LogResult, PlatformHealth
from .platforms import (
    BasePlatform,
    ConsolePlatform,
    FilePlatform,
    MockPlatform,
    WebhookPlatform,
)


class AgentLogger:
    def __init__(self, config: AgentLoggerConfig | str | Path | None = None):
        if isinstance(config, (str, Path)):
            self.config = AgentLoggerConfig.from_file(str(config))
        elif isinstance(config, AgentLoggerConfig):
            self.config = config
        else:
            self.config = AgentLoggerConfig.from_file("reskpoints.yaml")

        self.environment = self.config.environment
        self.host = platform.node()

        self.masker = FieldMasker(
            sensitive_fields=self.config.sensitive_fields,
            enabled=self.config.masking_enabled,
        )

        self.platforms: dict[str, BasePlatform] = {}
        self._init_platforms()

    def _init_platforms(self):
        platform_configs = self.config.platforms_config
        registry: dict[str, type[BasePlatform]] = {
            "console": ConsolePlatform,
            "file": FilePlatform,
            "webhook": WebhookPlatform,
        }

        try:
            from .platforms.prometheus import PrometheusPlatform
            registry["prometheus"] = PrometheusPlatform
        except ImportError:
            pass

        try:
            from .platforms.datadog import DatadogPlatform
            registry["datadog"] = DatadogPlatform
        except ImportError:
            pass

        for name, platform_cls in registry.items():
            cfg = platform_configs.get(name, {})
            if cfg.get("enabled", False):
                instance = platform_cls(cfg)
                self.platforms[name] = instance

        if not self.platforms:
            self.platforms["mock"] = MockPlatform({"enabled": True})

    def log(
        self,
        agent_id: str,
        action: str,
        probability: float = 1.0,
        params: dict[str, Any] | None = None,
        result: Any = None,
        success: bool = True,
        duration_ms: float | None = None,
        session_id: str | None = None,
        correlation_id: str | None = None,
        sensitive_fields: list[str] | None = None,
        **metadata: Any,
    ) -> list[LogResult]:
        entry = ActionLog(
            agent_id=agent_id,
            session_id=session_id,
            correlation_id=correlation_id,
            action=action,
            probability=probability,
            parameters=params or {},
            result=result,
            success=success,
            duration_ms=duration_ms,
            environment=self.environment,
            host=self.host,
            metadata=metadata,
            sensitive_fields=sensitive_fields or [],
        )
        return self.log_action(entry)

    def log_action(self, entry: ActionLog) -> list[LogResult]:
        rate = self.config.get_sampling_rate(entry.action)
        if rate < 1.0 and random.random() > rate:
            return [LogResult(success=True, platform="sampling_skip", action_id=entry.id)]

        if self.config.masking_enabled:
            entry.parameters = self.masker.mask(
                entry.parameters,
                extra_fields=entry.sensitive_fields,
            )

        results: list[LogResult] = []
        for platform in self.platforms.values():
            result = platform.emit(entry)
            results.append(result)
        return results

    async def alog(
        self,
        agent_id: str,
        action: str,
        probability: float = 1.0,
        params: dict[str, Any] | None = None,
        result: Any = None,
        success: bool = True,
        duration_ms: float | None = None,
        session_id: str | None = None,
        correlation_id: str | None = None,
        sensitive_fields: list[str] | None = None,
        **metadata: Any,
    ) -> list[LogResult]:
        entry = ActionLog(
            agent_id=agent_id,
            session_id=session_id,
            correlation_id=correlation_id,
            action=action,
            probability=probability,
            parameters=params or {},
            result=result,
            success=success,
            duration_ms=duration_ms,
            environment=self.environment,
            host=self.host,
            metadata=metadata,
            sensitive_fields=sensitive_fields or [],
        )
        return await self.alog_action(entry)

    async def alog_action(self, entry: ActionLog) -> list[LogResult]:
        rate = self.config.get_sampling_rate(entry.action)
        if rate < 1.0 and random.random() > rate:
            return [LogResult(success=True, platform="sampling_skip", action_id=entry.id)]

        if self.config.masking_enabled:
            entry.parameters = self.masker.mask(
                entry.parameters,
                extra_fields=entry.sensitive_fields,
            )

        import asyncio

        results: list[LogResult] = []
        tasks = [platform.aemit(entry) for platform in self.platforms.values()]
        for coro in asyncio.as_completed(tasks):
            result = await coro
            results.append(result)
        return results

    def flush(self):
        for platform in self.platforms.values():
            platform.flush()

    def health(self) -> dict[str, Any]:
        return {
            platform_name: platform.health().to_dict()
            for platform_name, platform in self.platforms.items()
        }

    def get_platform(self, name: str) -> BasePlatform | None:
        return self.platforms.get(name)
