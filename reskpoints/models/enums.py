"""Enums for AI metrics and error types."""

from enum import Enum


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class MetricType(str, Enum):
    """Types of AI metrics."""
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    ACCURACY = "accuracy"
    TOKEN_USAGE = "token_usage"
    COST = "cost"
    AVAILABILITY = "availability"
    CUSTOM = "custom"


class AIProvider(str, Enum):
    """AI service providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE = "azure"
    AWS = "aws"
    HUGGINGFACE = "huggingface"
    CUSTOM = "custom"


class ModelSize(str, Enum):
    """AI model size categories."""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    EXTRA_LARGE = "xl"


class ErrorCategory(str, Enum):
    """Categories of AI errors."""
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    INVALID_INPUT = "invalid_input"
    MODEL_ERROR = "model_error"
    NETWORK_ERROR = "network_error"
    QUOTA_EXCEEDED = "quota_exceeded"
    SERVICE_UNAVAILABLE = "service_unavailable"
    UNKNOWN = "unknown"