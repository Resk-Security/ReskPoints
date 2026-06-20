import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ActionLog:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    agent_id: str = ""
    session_id: str | None = None
    correlation_id: str | None = None
    action: str = ""
    probability: float = 1.0
    parameters: dict[str, Any] = field(default_factory=dict)
    result: Any = None
    success: bool = True
    duration_ms: float | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    environment: str = ""
    host: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    sensitive_fields: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "id": self.id,
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "correlation_id": self.correlation_id,
            "action": self.action,
            "probability": self.probability,
            "parameters": self.parameters,
            "result": self.result,
            "success": self.success,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp.isoformat(),
            "environment": self.environment,
            "host": self.host,
            "metadata": self.metadata,
        }
        if self.sensitive_fields:
            d["has_sensitive_fields"] = True
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ActionLog":
        ts = data.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        return cls(
            id=data.get("id", uuid.uuid4().hex[:16]),
            agent_id=data.get("agent_id", ""),
            session_id=data.get("session_id"),
            correlation_id=data.get("correlation_id"),
            action=data.get("action", ""),
            probability=float(data.get("probability", 1.0)),
            parameters=data.get("parameters", {}),
            result=data.get("result"),
            success=bool(data.get("success", True)),
            duration_ms=data.get("duration_ms"),
            timestamp=ts or datetime.now(timezone.utc),
            environment=data.get("environment", ""),
            host=data.get("host", ""),
            metadata=data.get("metadata", {}),
            sensitive_fields=data.get("sensitive_fields", []),
        )


@dataclass
class LogResult:
    success: bool
    platform: str
    action_id: str | None = None
    error: str | None = None
    duration_ms: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "platform": self.platform,
            "action_id": self.action_id,
            "error": self.error,
            "duration_ms": self.duration_ms,
        }


@dataclass
class PlatformHealth:
    platform: str
    status: str  # "ok" | "degraded" | "down"
    latency_ms: float | None = None
    error: str | None = None
    queue_size: int = 0
    last_success: datetime | None = None
    last_failure: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "platform": self.platform,
            "status": self.status,
            "latency_ms": self.latency_ms,
            "error": self.error,
            "queue_size": self.queue_size,
        }
