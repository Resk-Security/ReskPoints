"""Database connection utilities for ReskPoints."""

import asyncio
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

import asyncpg
from asyncpg import Pool, Connection
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from reskpoints.core.config import settings
from reskpoints.core.logging import get_logger

logger = get_logger(__name__)

# SQLAlchemy base for ORM models
Base = declarative_base()

# Global connection pools
_postgres_pool: Optional[Pool] = None
_timescale_pool: Optional[Pool] = None
_async_engine = None
_async_session_maker = None


class DatabaseConnection:
    """Async database connection manager."""
    
    def __init__(self):
        self.postgres_pool: Optional[Pool] = None
        self.timescale_pool: Optional[Pool] = None
        
    async def connect_postgres(self) -> Pool:
        """Connect to PostgreSQL database."""
        if not settings.DATABASE_URL:
            raise ValueError("DATABASE_URL not configured")
            
        try:
            self.postgres_pool = await asyncpg.create_pool(
                settings.DATABASE_URL,
                min_size=5,
                max_size=20,
                command_timeout=60,
                server_settings={
                    'application_name': 'reskpoints_api',
                }
            )
            logger.info("Connected to PostgreSQL database")
            return self.postgres_pool
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    async def connect_timescale(self) -> Pool:
        """Connect to TimescaleDB database."""
        if not settings.TIMESCALE_URL:
            raise ValueError("TIMESCALE_URL not configured")
            
        try:
            self.timescale_pool = await asyncpg.create_pool(
                settings.TIMESCALE_URL,
                min_size=5,
                max_size=20,
                command_timeout=60,
                server_settings={
                    'application_name': 'reskpoints_metrics',
                }
            )
            logger.info("Connected to TimescaleDB database")
            return self.timescale_pool
        except Exception as e:
            logger.error(f"Failed to connect to TimescaleDB: {e}")
            raise
    
    async def close(self):
        """Close all database connections."""
        if self.postgres_pool:
            await self.postgres_pool.close()
            logger.info("Closed PostgreSQL connection pool")
            
        if self.timescale_pool:
            await self.timescale_pool.close()
            logger.info("Closed TimescaleDB connection pool")


# Global database connection instance
db_connection = DatabaseConnection()


async def init_database_connections():
    """Initialize all database connections."""
    global _postgres_pool, _timescale_pool, _async_engine, _async_session_maker
    
    try:
        # Initialize connection pools
        if settings.DATABASE_URL:
            _postgres_pool = await db_connection.connect_postgres()
        
        if settings.TIMESCALE_URL:
            _timescale_pool = await db_connection.connect_timescale()
        
        # Initialize SQLAlchemy async engine
        if settings.DATABASE_URL:
            _async_engine = create_async_engine(
                settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
                echo=settings.DEBUG,
                pool_size=20,
                max_overflow=30,
                pool_pre_ping=True,
            )
            _async_session_maker = async_sessionmaker(
                _async_engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
            
        logger.info("Database connections initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database connections: {e}")
        raise


async def close_database_connections():
    """Close all database connections."""
    global _postgres_pool, _timescale_pool, _async_engine
    
    await db_connection.close()
    
    if _async_engine:
        await _async_engine.dispose()
        logger.info("Closed SQLAlchemy async engine")
    
    _postgres_pool = None
    _timescale_pool = None
    _async_engine = None


@asynccontextmanager
async def get_postgres_connection():
    """Get PostgreSQL database connection from pool."""
    if not _postgres_pool:
        raise RuntimeError("PostgreSQL pool not initialized")
    
    async with _postgres_pool.acquire() as connection:
        try:
            yield connection
        except Exception as e:
            logger.error(f"Database error: {e}")
            raise


@asynccontextmanager
async def get_timescale_connection():
    """Get TimescaleDB database connection from pool."""
    if not _timescale_pool:
        raise RuntimeError("TimescaleDB pool not initialized")
    
    async with _timescale_pool.acquire() as connection:
        try:
            yield connection
        except Exception as e:
            logger.error(f"TimescaleDB error: {e}")
            raise


@asynccontextmanager
async def get_async_session():
    """Get SQLAlchemy async session."""
    if not _async_session_maker:
        raise RuntimeError("Async session maker not initialized")
    
    async with _async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


async def execute_query(
    query: str,
    params: Optional[Dict[str, Any]] = None,
    use_timescale: bool = False,
) -> Any:
    """Execute a query on the specified database."""
    connection_manager = get_timescale_connection if use_timescale else get_postgres_connection
    
    async with connection_manager() as connection:
        if params:
            result = await connection.fetch(query, *params.values())
        else:
            result = await connection.fetch(query)
        return result


async def execute_command(
    command: str,
    params: Optional[Dict[str, Any]] = None,
    use_timescale: bool = False,
) -> str:
    """Execute a command on the specified database."""
    connection_manager = get_timescale_connection if use_timescale else get_postgres_connection
    
    async with connection_manager() as connection:
        if params:
            result = await connection.execute(command, *params.values())
        else:
            result = await connection.execute(command)
        return result