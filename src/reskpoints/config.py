import os
import re
from pathlib import Path
from typing import Any

import yaml


_ENV_VAR_RE = re.compile(r"\$\{([^}:]+)(?::([^}]*))?\}")


def _resolve_env(value: str) -> str:
    def _replace(m: re.Match) -> str:
        var = m.group(1)
        default = m.group(2)
        return os.environ.get(var, default) if default else os.environ.get(var, "")

    return _ENV_VAR_RE.sub(_replace, value)


def _resolve_env_recursive(obj: Any) -> Any:
    if isinstance(obj, str):
        return _resolve_env(obj) if "${" in obj else obj
    if isinstance(obj, dict):
        return {k: _resolve_env_recursive(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_resolve_env_recursive(v) for v in obj]
    return obj


DEFAULT_CONFIG = {
    "agent_logger": {
        "environment": "${ENV:development}",
        "masking": {
            "enabled": True,
            "sensitive_fields": [
                "api_key",
                "password",
                "token",
                "secret",
                "authorization",
            ],
        },
        "sampling": {
            "default_rate": 1.0,
            "rules": [],
        },
        "buffering": {
            "max_size": 1000,
            "flush_interval": 5.0,
        },
        "retry": {
            "max_attempts": 3,
            "backoff": [0.5, 1.5, 4.5],
            "circuit_breaker": {
                "threshold": 5,
                "recovery_time": 30,
            },
        },
        "platforms": {
            "console": {
                "enabled": True,
                "format": "human",
            },
        },
    }
}


class AgentLoggerConfig:
    def __init__(self, config: dict[str, Any] | None = None):
        resolved = _resolve_env_recursive(config or {})
        self._raw = resolved

        section = resolved.get("agent_logger", {})
        self.environment = section.get("environment", "development")
        self.masking_config = section.get("masking", {})
        self.sampling_config = section.get("sampling", {})
        self.buffering_config = section.get("buffering", {})
        self.retry_config = section.get("retry", {})
        self.platforms_config = section.get("platforms", {})

    @property
    def masking_enabled(self) -> bool:
        return self.masking_config.get("enabled", True)

    @property
    def sensitive_fields(self) -> list[str]:
        return self.masking_config.get("sensitive_fields", [])

    @property
    def default_rate(self) -> float:
        return float(self.sampling_config.get("default_rate", 1.0))

    @property
    def sampling_rules(self) -> list[dict[str, Any]]:
        return self.sampling_config.get("rules", [])

    def get_sampling_rate(self, action: str) -> float:
        for rule in self.sampling_rules:
            pattern = rule.get("action", "")
            if pattern == action or (pattern.endswith("*") and action.startswith(pattern[:-1])):
                return float(rule.get("rate", self.default_rate))
        return self.default_rate

    def get_platform_config(self, name: str) -> dict[str, Any]:
        return self.platforms_config.get(name, {})

    @classmethod
    def from_file(cls, path: str | Path) -> "AgentLoggerConfig":
        path = Path(path)
        if path.exists():
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        else:
            data = {}
        merged = {**DEFAULT_CONFIG, **(data or {})}
        return cls(merged)

    def to_dict(self) -> dict[str, Any]:
        return self._raw
