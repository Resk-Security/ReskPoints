"""Main application entry point for ReskPoints."""

import asyncio
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

from reskpoints.core.config import settings
from reskpoints.core.logging import setup_logging, get_logger
from reskpoints.api.v1.router import api_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    setup_logging()
    logger.info("Starting ReskPoints application...")
    
    # Initialize database connections
    try:
        if settings.DATABASE_URL or settings.TIMESCALE_URL:
            from reskpoints.infrastructure.database.connection import init_database_connections
            await init_database_connections()
            logger.info("Database connections initialized")
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}")
    
    # Initialize ClickHouse for analytics
    try:
        if settings.CLICKHOUSE_URL:
            from reskpoints.infrastructure.database.clickhouse import init_clickhouse
            await init_clickhouse()
            logger.info("ClickHouse initialized")
    except Exception as e:
        logger.warning(f"ClickHouse initialization failed: {e}")
    
    # Initialize Redis cache
    try:
        if settings.REDIS_URL:
            from reskpoints.infrastructure.cache.redis import init_cache
            await init_cache()
            logger.info("Redis cache initialized")
    except Exception as e:
        logger.warning(f"Redis cache initialization failed: {e}")
    
    # Start metrics collector
    try:
        from reskpoints.services.metrics.collector import start_metrics_collector
        await start_metrics_collector()
        logger.info("Metrics collector started")
    except Exception as e:
        logger.warning(f"Metrics collector initialization failed: {e}")
    
    # Start monitoring services
    try:
        from reskpoints.services.monitoring.metrics import start_monitoring_tasks
        await start_monitoring_tasks()
        logger.info("Monitoring services started")
    except Exception as e:
        logger.warning(f"Monitoring services initialization failed: {e}")
    
    # Start incident monitoring
    try:
        from reskpoints.services.incident.manager import start_incident_monitoring
        await start_incident_monitoring()
        logger.info("Incident monitoring started")
    except Exception as e:
        logger.warning(f"Incident monitoring initialization failed: {e}")
    
    logger.info("ReskPoints application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down ReskPoints application...")
    
    try:
        from reskpoints.services.metrics.collector import stop_metrics_collector
        await stop_metrics_collector()
        logger.info("Metrics collector stopped")
    except Exception as e:
        logger.warning(f"Error stopping metrics collector: {e}")
    
    try:
        from reskpoints.infrastructure.database.connection import close_database_connections
        await close_database_connections()
        logger.info("Database connections closed")
    except Exception as e:
        logger.warning(f"Error closing database connections: {e}")
    
    try:
        from reskpoints.infrastructure.database.clickhouse import close_clickhouse
        await close_clickhouse()
        logger.info("ClickHouse connection closed")
    except Exception as e:
        logger.warning(f"Error closing ClickHouse: {e}")
    
    try:
        from reskpoints.infrastructure.cache.redis import close_cache
        await close_cache()
        logger.info("Redis cache closed")
    except Exception as e:
        logger.warning(f"Error closing Redis cache: {e}")
    
    logger.info("ReskPoints application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="ReskPoints",
        description="AI metrics monitoring and cost tracking system",
        version="0.1.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )
    
    # Include API routes
    app.include_router(api_router, prefix="/api/v1")
    
    return app


def main() -> None:
    """Main entry point."""
    app = create_app()
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_level="info" if settings.DEBUG else "warning",
        reload=settings.DEBUG,
    )


if __name__ == "__main__":
    main()