"""Test configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient

from reskpoints.main import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def sample_ai_metric():
    """Sample AI metric for testing."""
    from reskpoints.models.metrics import AIMetric
    from reskpoints.models.enums import MetricType, AIProvider
    
    return AIMetric(
        metric_type=MetricType.LATENCY,
        value=150.5,
        unit="ms",
        provider=AIProvider.OPENAI,
        model_name="gpt-3.5-turbo",
        endpoint="/v1/chat/completions",
        user_id="user_123",
        project_id="project_456",
    )


@pytest.fixture
def sample_ai_error():
    """Sample AI error for testing."""
    from reskpoints.models.metrics import AIError
    from reskpoints.models.enums import ErrorSeverity, ErrorCategory, AIProvider
    
    return AIError(
        severity=ErrorSeverity.HIGH,
        category=ErrorCategory.RATE_LIMIT,
        message="Rate limit exceeded",
        code="rate_limit_exceeded",
        provider=AIProvider.OPENAI,
        model_name="gpt-3.5-turbo",
        endpoint="/v1/chat/completions",
        user_id="user_123",
    )


@pytest.fixture
def sample_transaction():
    """Sample transaction for testing."""
    from reskpoints.models.cost import Transaction, TokenUsage, CostBreakdown
    from reskpoints.models.enums import AIProvider
    from decimal import Decimal
    
    return Transaction(
        provider=AIProvider.OPENAI,
        model_name="gpt-3.5-turbo",
        endpoint="/v1/chat/completions",
        user_id="user_123",
        project_id="project_456",
        duration_ms=1250.0,
        status_code=200,
        success=True,
        token_usage=TokenUsage(
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
        ),
        cost_breakdown=CostBreakdown(
            input_cost=Decimal("0.002"),
            output_cost=Decimal("0.003"),
            total_cost=Decimal("0.005"),
        ),
    )