"""Test metrics data models."""

import pytest
from datetime import datetime
from decimal import Decimal

from reskpoints.models.metrics import AIMetric, AIError, ModelMetrics
from reskpoints.models.enums import MetricType, AIProvider, ErrorSeverity, ErrorCategory


def test_ai_metric_creation(sample_ai_metric):
    """Test AI metric creation and validation."""
    metric = sample_ai_metric
    
    assert metric.metric_type == MetricType.LATENCY
    assert metric.value == 150.5
    assert metric.unit == "ms"
    assert metric.provider == AIProvider.OPENAI
    assert metric.model_name == "gpt-3.5-turbo"
    assert metric.endpoint == "/v1/chat/completions"
    assert metric.user_id == "user_123"
    assert metric.project_id == "project_456"
    assert isinstance(metric.timestamp, datetime)


def test_ai_metric_negative_value():
    """Test AI metric validation with negative value."""
    with pytest.raises(ValueError, match="Metric value cannot be negative"):
        AIMetric(
            metric_type=MetricType.LATENCY,
            value=-10.0,
            unit="ms",
            provider=AIProvider.OPENAI,
            model_name="gpt-3.5-turbo",
            endpoint="/v1/chat/completions",
        )


def test_ai_error_creation(sample_ai_error):
    """Test AI error creation and validation."""
    error = sample_ai_error
    
    assert error.severity == ErrorSeverity.HIGH
    assert error.category == ErrorCategory.RATE_LIMIT
    assert error.message == "Rate limit exceeded"
    assert error.code == "rate_limit_exceeded"
    assert error.provider == AIProvider.OPENAI
    assert error.model_name == "gpt-3.5-turbo"
    assert error.endpoint == "/v1/chat/completions"
    assert error.user_id == "user_123"
    assert isinstance(error.timestamp, datetime)
    assert not error.resolved


def test_model_metrics_error_rate_validation():
    """Test model metrics error rate validation."""
    # Valid error rate
    metrics = ModelMetrics(
        provider=AIProvider.OPENAI,
        model_name="gpt-3.5-turbo",
        time_window_start=datetime.utcnow(),
        time_window_end=datetime.utcnow(),
        error_rate=15.5,
    )
    assert metrics.error_rate == 15.5
    
    # Invalid error rate - too high
    with pytest.raises(ValueError, match="Error rate must be between 0 and 100"):
        ModelMetrics(
            provider=AIProvider.OPENAI,
            model_name="gpt-3.5-turbo",
            time_window_start=datetime.utcnow(),
            time_window_end=datetime.utcnow(),
            error_rate=150.0,
        )
    
    # Invalid error rate - negative
    with pytest.raises(ValueError, match="Error rate must be between 0 and 100"):
        ModelMetrics(
            provider=AIProvider.OPENAI,
            model_name="gpt-3.5-turbo",
            time_window_start=datetime.utcnow(),
            time_window_end=datetime.utcnow(),
            error_rate=-5.0,
        )