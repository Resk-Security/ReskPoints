import json
from pathlib import Path
from typing import Any

from ..models import ActionLog, LogResult
from .base import BasePlatform


class FilePlatform(BasePlatform):
    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        path_str = self.config.get("path", "/var/log/agent_actions.jsonl")
        self.path = Path(path_str)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _emit(self, entry: ActionLog) -> LogResult:
        data = entry.to_dict()
        data["timestamp"] = entry.timestamp.isoformat()
        line = json.dumps(data, default=str)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        return LogResult(success=True, platform=self.name, action_id=entry.id)
