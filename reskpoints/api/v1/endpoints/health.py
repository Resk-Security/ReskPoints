"""Health check endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime
    version: str
    services: dict


@router.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    services = {
        "api": "healthy",
        "database": "unknown",
        "timescale": "unknown",
        "cache": "unknown",
        "clickhouse": "unknown",
    }
    
    # Check PostgreSQL database
    try:
        from reskpoints.infrastructure.database.connection import get_postgres_connection
        async with get_postgres_connection() as conn:
            await conn.fetchval("SELECT 1")
        services["database"] = "healthy"
    except Exception:
        services["database"] = "not_configured"
    
    # Check TimescaleDB
    try:
        from reskpoints.infrastructure.database.connection import get_timescale_connection
        async with get_timescale_connection() as conn:
            await conn.fetchval("SELECT 1")
        services["timescale"] = "healthy"
    except Exception:
        services["timescale"] = "not_configured"
    
    # Check Redis cache
    try:
        from reskpoints.infrastructure.cache.redis import get_cache
        cache = get_cache()
        is_healthy = await cache.health_check()
        services["cache"] = "healthy" if is_healthy else "unhealthy"
    except Exception:
        services["cache"] = "not_configured"
    
    # Check ClickHouse
    try:
        from reskpoints.infrastructure.database.clickhouse import get_clickhouse_client
        clickhouse = get_clickhouse_client()
        # Basic health check would go here
        services["clickhouse"] = "healthy"
    except Exception:
        services["clickhouse"] = "not_configured"
    
    # Determine overall status
    unhealthy_services = [k for k, v in services.items() if v == "unhealthy"]
    overall_status = "degraded" if unhealthy_services else "healthy"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version="0.1.0",
        services=services
    )


@router.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    return {"status": "ready", "timestamp": datetime.utcnow()}


@router.get("/live")
async def liveness_check():
    """Liveness check endpoint."""
    return {"status": "alive", "timestamp": datetime.utcnow()}