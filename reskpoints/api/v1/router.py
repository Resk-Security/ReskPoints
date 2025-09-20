"""API v1 router."""

from fastapi import APIRouter

from reskpoints.api.v1.endpoints import health, metrics, cost, incidents

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
api_router.include_router(cost.router, prefix="/cost", tags=["cost"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])