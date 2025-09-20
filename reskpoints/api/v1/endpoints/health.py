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
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="0.1.0",
        services={
            "api": "healthy",
            "database": "not_configured",
            "cache": "not_configured",
        }
    )


@router.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    return {"status": "ready", "timestamp": datetime.utcnow()}


@router.get("/live")
async def liveness_check():
    """Liveness check endpoint."""
    return {"status": "alive", "timestamp": datetime.utcnow()}