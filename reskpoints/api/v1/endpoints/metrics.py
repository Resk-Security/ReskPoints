"""Metrics API endpoints."""

from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from reskpoints.models.metrics import AIMetric, AIError, ModelMetrics
from reskpoints.models.enums import MetricType, AIProvider, ErrorSeverity

router = APIRouter()


# Response models
class MetricsResponse(BaseModel):
    """Metrics list response."""
    metrics: List[AIMetric]
    total: int
    page: int
    per_page: int


class ErrorsResponse(BaseModel):
    """Errors list response."""
    errors: List[AIError]
    total: int
    page: int
    per_page: int


@router.post("/submit", response_model=AIMetric)
async def submit_metric(metric: AIMetric):
    """Submit a new AI metric."""
    try:
        # Try to use metrics collector if available
        try:
            from reskpoints.services.metrics.collector import get_metrics_collector
            collector = get_metrics_collector()
            success = await collector.collect_metric(metric)
            
            if not success:
                raise HTTPException(status_code=500, detail="Failed to collect metric")
        except ImportError:
            # Fallback if metrics collector not available
            pass
        
        # Generate ID for response
        metric.id = f"metric_{datetime.utcnow().timestamp()}"
        return metric
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting metric: {e}")


@router.get("/", response_model=MetricsResponse)
async def list_metrics(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=1000, description="Items per page"),
    metric_type: Optional[MetricType] = Query(None, description="Filter by metric type"),
    provider: Optional[AIProvider] = Query(None, description="Filter by provider"),
    start_time: Optional[datetime] = Query(None, description="Start time filter"),
    end_time: Optional[datetime] = Query(None, description="End time filter"),
):
    """List AI metrics with filtering and pagination."""
    # TODO: Implement actual database query with the new infrastructure
    # For now, return empty list with proper structure
    return MetricsResponse(
        metrics=[],
        total=0,
        page=page,
        per_page=per_page,
    )


@router.get("/{metric_id}", response_model=AIMetric)
async def get_metric(metric_id: str):
    """Get a specific metric by ID."""
    # TODO: Implement metric retrieval from database
    raise HTTPException(status_code=404, detail="Metric not found")


@router.post("/errors", response_model=AIError)
async def submit_error(error: AIError):
    """Submit a new AI error."""
    try:
        # Try to use metrics collector if available
        try:
            from reskpoints.services.metrics.collector import get_metrics_collector
            collector = get_metrics_collector()
            success = await collector.collect_error(error)
            
            if not success:
                raise HTTPException(status_code=500, detail="Failed to collect error")
        except ImportError:
            # Fallback if metrics collector not available
            pass
        
        # Generate ID for response
        error.id = f"error_{datetime.utcnow().timestamp()}"
        return error
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting error: {e}")


@router.get("/errors", response_model=ErrorsResponse)
async def list_errors(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=1000, description="Items per page"),
    severity: Optional[ErrorSeverity] = Query(None, description="Filter by severity"),
    provider: Optional[AIProvider] = Query(None, description="Filter by provider"),
    resolved: Optional[bool] = Query(None, description="Filter by resolution status"),
    start_time: Optional[datetime] = Query(None, description="Start time filter"),
    end_time: Optional[datetime] = Query(None, description="End time filter"),
):
    """List AI errors with filtering and pagination."""
    # TODO: Implement actual database query
    return ErrorsResponse(
        errors=[],
        total=0,
        page=page,
        per_page=per_page,
    )


@router.get("/errors/{error_id}", response_model=AIError)
async def get_error(error_id: str):
    """Get a specific error by ID."""
    # TODO: Implement error retrieval
    raise HTTPException(status_code=404, detail="Error not found")


@router.get("/models/{provider}/{model_name}", response_model=ModelMetrics)
async def get_model_metrics(
    provider: AIProvider,
    model_name: str,
    start_time: Optional[datetime] = Query(None, description="Start time for metrics"),
    end_time: Optional[datetime] = Query(None, description="End time for metrics"),
):
    """Get aggregated metrics for a specific model."""
    try:
        # Try to use metrics collector if available
        try:
            from reskpoints.services.metrics.collector import get_metrics_collector
            collector = get_metrics_collector()
            metrics = await collector.get_model_metrics(
                provider.value,
                model_name,
                start_time,
                end_time,
            )
            return metrics
        except ImportError:
            # Fallback if metrics collector not available
            start = start_time or datetime.utcnow() - timedelta(hours=24)
            end = end_time or datetime.utcnow()
            
            return ModelMetrics(
                provider=provider,
                model_name=model_name,
                time_window_start=start,
                time_window_end=end,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
            )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting model metrics: {e}")