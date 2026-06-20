from .agent_logger import AgentLogger
from .config import AgentLoggerConfig
from .decorator import log_action
from .masking import FieldMasker
from .models import ActionLog, LogResult
from .platforms import (
    BasePlatform,
    ConsolePlatform,
    FilePlatform,
    MockPlatform,
    WebhookPlatform,
)

__version__ = "0.1.0"
__author__ = "RESK Security"

__all__ = [
    "AgentLogger",
    "AgentLoggerConfig",
    "log_action",
    "FieldMasker",
    "ActionLog",
    "LogResult",
    "BasePlatform",
    "ConsolePlatform",
    "FilePlatform",
    "MockPlatform",
    "WebhookPlatform",
]
