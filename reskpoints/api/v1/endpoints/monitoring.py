"""Monitoring and observability API endpoints."""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from reskpoints.services.monitoring.metrics import (
    get_monitoring_service,
    get_alert_manager,
    get_performance_profiler,
    MonitoringService,
    AlertManager,
    PerformanceProfiler,
)
from reskpoints.api.middleware.auth import require_admin, User

router = APIRouter()


class SystemHealthResponse(BaseModel):
    """System health response model."""
    uptime_seconds: float
    timestamp: str
    average_latencies: Dict[str, float]
    error_rates: Dict[str, float]
    system_status: str


class AlertResponse(BaseModel):
    """Alert response model."""
    id: str
    name: str
    severity: str
    description: str
    timestamp: str
    active: bool


class PerformanceSummaryResponse(BaseModel):
    """Performance summary response model."""
    total_operations: int
    operations: Dict[str, Dict[str, float]]
    slow_queries: List[Dict[str, Any]]


@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health(
    monitoring: MonitoringService = Depends(get_monitoring_service)
):
    """Get comprehensive system health metrics."""
    health_data = monitoring.get_system_health()
    return SystemHealthResponse(**health_data)


@router.get("/metrics")
async def get_prometheus_metrics(
    monitoring: MonitoringService = Depends(get_monitoring_service)
):
    """Get Prometheus metrics in text format."""
    metrics_text = monitoring.get_prometheus_metrics()
    return Response(content=metrics_text, media_type="text/plain")


@router.get("/alerts", response_model=List[AlertResponse])
async def get_active_alerts(
    admin_user: User = Depends(require_admin),
    alert_manager: AlertManager = Depends(get_alert_manager)
):
    """Get all active alerts (admin only)."""
    alerts = alert_manager.get_active_alerts()
    return [AlertResponse(**alert) for alert in alerts]


@router.get("/alerts/history", response_model=List[AlertResponse])
async def get_alert_history(
    admin_user: User = Depends(require_admin),
    alert_manager: AlertManager = Depends(get_alert_manager),
    limit: int = 100
):
    """Get alert history (admin only)."""
    alerts = alert_manager.get_alert_history(limit)
    return [AlertResponse(**alert) for alert in alerts]


@router.get("/performance", response_model=PerformanceSummaryResponse)
async def get_performance_summary(
    admin_user: User = Depends(require_admin),
    profiler: PerformanceProfiler = Depends(get_performance_profiler)
):
    """Get performance profiling summary (admin only)."""
    summary = profiler.get_performance_summary()
    return PerformanceSummaryResponse(**summary)


@router.post("/alerts/check")
async def trigger_alert_check(
    admin_user: User = Depends(require_admin),
    alert_manager: AlertManager = Depends(get_alert_manager)
):
    """Manually trigger alert check (admin only)."""
    await alert_manager.check_alerts()
    return {"message": "Alert check triggered"}


@router.get("/stats")
async def get_system_stats(
    monitoring: MonitoringService = Depends(get_monitoring_service)
):
    """Get basic system statistics."""
    health = monitoring.get_system_health()
    
    return {
        "uptime": health["uptime_seconds"],
        "status": health["system_status"],
        "timestamp": health["timestamp"],
        "metrics": {
            "total_endpoints": len(health["average_latencies"]),
            "avg_response_time": (
                sum(health["average_latencies"].values()) / len(health["average_latencies"])
                if health["average_latencies"] else 0
            ),
            "total_error_sources": len(health["error_rates"]),
        }
    }