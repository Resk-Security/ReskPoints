"""Main application entry point for ReskPoints."""

import asyncio
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

from reskpoints.core.config import settings
from reskpoints.core.logging import setup_logging
from reskpoints.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    setup_logging()
    
    # TODO: Initialize database connections
    # TODO: Initialize Redis cache
    # TODO: Initialize monitoring
    
    yield
    
    # Shutdown
    # TODO: Close database connections
    # TODO: Close Redis cache


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