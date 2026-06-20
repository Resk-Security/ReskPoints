import json
import sys
from datetime import datetime
from typing import Any

from ..models import ActionLog, LogResult
from .base import BasePlatform


class ConsolePlatform(BasePlatform):
    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.format = self.config.get("format", "human")

    def _emit(self, entry: ActionLog) -> LogResult:
        if self.format == "json":
            data = entry.to_dict()
            data["timestamp"] = entry.timestamp.isoformat()
            print(json.dumps(data, default=str), file=sys.stdout, flush=True)
        else:
            ts = entry.timestamp.strftime("%H:%M:%S.%f")[:-3]
            prob = f"p={entry.probability:.2f}" if entry.probability < 1.0 else ""
            status = "✓" if entry.success else "✗"
            print(
                f"[{ts}] {status} {entry.agent_id} | {entry.action} {prob}"
                f" | params={_truncate(entry.parameters)}"
                f" | result={_truncate(entry.result)}",
                file=sys.stdout,
                flush=True,
            )
        return LogResult(success=True, platform=self.name, action_id=entry.id)


def _truncate(v: Any, max_len: int = 80) -> str:
    s = json.dumps(v, default=str) if not isinstance(v, str) else v
    return s[:max_len] + "..." if len(s) > max_len else s
