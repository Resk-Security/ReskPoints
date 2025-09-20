"""AI metrics data models."""

from datetime import datetime
from typing import Dict, Any, Optional
from decimal import Decimal

from pydantic import BaseModel, Field, validator

from reskpoints.models.enums import MetricType, AIProvider, ModelSize, ErrorSeverity, ErrorCategory


class AIMetric(BaseModel):
    """AI metric data model."""
    
    id: Optional[str] = Field(None, description="Unique metric identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Metric timestamp")
    metric_type: MetricType = Field(..., description="Type of metric")
    value: float = Field(..., description="Metric value")
    unit: str = Field(..., description="Metric unit")
    
    # Context information
    provider: AIProvider = Field(..., description="AI service provider")
    model_name: str = Field(..., description="AI model name")
    model_size: Optional[ModelSize] = Field(None, description="Model size category")
    endpoint: str = Field(..., description="API endpoint")
    
    # Additional metadata
    user_id: Optional[str] = Field(None, description="User identifier")
    project_id: Optional[str] = Field(None, description="Project identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    request_id: Optional[str] = Field(None, description="Request identifier")
    
    # Custom tags and metadata
    tags: Dict[str, str] = Field(default_factory=dict, description="Custom tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('value')
    def validate_value(cls, v):
        """Validate metric value."""
        if v < 0:
            raise ValueError("Metric value cannot be negative")
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class AIError(BaseModel):
    """AI error data model."""
    
    id: Optional[str] = Field(None, description="Unique error identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    severity: ErrorSeverity = Field(..., description="Error severity level")
    category: ErrorCategory = Field(..., description="Error category")
    
    # Error details
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")
    details: Dict[str, Any] = Field(default_factory=dict, description="Error details")
    
    # Context information
    provider: AIProvider = Field(..., description="AI service provider")
    model_name: str = Field(..., description="AI model name")
    endpoint: str = Field(..., description="API endpoint")
    
    # Request context
    user_id: Optional[str] = Field(None, description="User identifier")
    project_id: Optional[str] = Field(None, description="Project identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    request_id: Optional[str] = Field(None, description="Request identifier")
    
    # Stack trace and debugging info
    stack_trace: Optional[str] = Field(None, description="Stack trace")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracking")
    
    # Resolution tracking
    resolved: bool = Field(default=False, description="Whether error is resolved")
    resolution_notes: Optional[str] = Field(None, description="Resolution notes")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")
    
    # Custom tags and metadata
    tags: Dict[str, str] = Field(default_factory=dict, description="Custom tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class ModelMetrics(BaseModel):
    """Aggregated model metrics."""
    
    provider: AIProvider = Field(..., description="AI service provider")
    model_name: str = Field(..., description="AI model name")
    time_window_start: datetime = Field(..., description="Time window start")
    time_window_end: datetime = Field(..., description="Time window end")
    
    # Performance metrics
    total_requests: int = Field(default=0, description="Total number of requests")
    successful_requests: int = Field(default=0, description="Number of successful requests")
    failed_requests: int = Field(default=0, description="Number of failed requests")
    
    # Latency metrics
    avg_latency_ms: Optional[float] = Field(None, description="Average latency in milliseconds")
    p50_latency_ms: Optional[float] = Field(None, description="50th percentile latency")
    p95_latency_ms: Optional[float] = Field(None, description="95th percentile latency")
    p99_latency_ms: Optional[float] = Field(None, description="99th percentile latency")
    
    # Throughput metrics
    requests_per_second: Optional[float] = Field(None, description="Requests per second")
    tokens_per_second: Optional[float] = Field(None, description="Tokens per second")
    
    # Error metrics
    error_rate: Optional[float] = Field(None, description="Error rate percentage")
    
    # Cost metrics
    total_cost_usd: Optional[Decimal] = Field(None, description="Total cost in USD")
    avg_cost_per_request: Optional[Decimal] = Field(None, description="Average cost per request")
    
    # Token metrics
    total_tokens: Optional[int] = Field(None, description="Total tokens processed")
    avg_tokens_per_request: Optional[float] = Field(None, description="Average tokens per request")
    
    @validator('error_rate')
    def validate_error_rate(cls, v):
        """Validate error rate percentage."""
        if v is not None and (v < 0 or v > 100):
            raise ValueError("Error rate must be between 0 and 100")
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v),
        }