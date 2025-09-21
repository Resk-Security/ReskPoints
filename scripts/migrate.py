#!/usr/bin/env python3
"""Database migration script for ReskPoints."""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reskpoints.infrastructure.database.connection import init_database_connections
from reskpoints.infrastructure.database.migrations import run_migrations
from reskpoints.infrastructure.database.clickhouse import init_clickhouse
from reskpoints.core.config import settings


async def main():
    """Run database migrations."""
    print("🚀 Starting ReskPoints database migrations...")
    
    try:
        # Initialize database connections
        print("📡 Initializing database connections...")
        await init_database_connections()
        
        # Run PostgreSQL and TimescaleDB migrations
        print("📊 Running PostgreSQL/TimescaleDB migrations...")
        await run_migrations()
        
        # Initialize ClickHouse
        if settings.CLICKHOUSE_URL:
            print("📈 Initializing ClickHouse...")
            await init_clickhouse()
        
        print("✅ All migrations completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())