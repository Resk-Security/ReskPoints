"""ClickHouse client for analytics and cost tracking."""

import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

import clickhouse_connect
from clickhouse_connect.driver import Client

from reskpoints.core.config import settings
from reskpoints.core.logging import get_logger

logger = get_logger(__name__)

# Global ClickHouse client
_clickhouse_client: Optional[Client] = None


class ClickHouseClient:
    """Async ClickHouse client with batch insert optimization."""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.batch_buffer: List[Dict[str, Any]] = []
        self.max_batch_size = 1000
        self.flush_interval = 30  # seconds
        
    async def connect(self):
        """Connect to ClickHouse database."""
        if not settings.CLICKHOUSE_URL:
            raise ValueError("CLICKHOUSE_URL not configured")
            
        try:
            # Parse ClickHouse URL
            url_parts = settings.CLICKHOUSE_URL.replace("http://", "").replace("https://", "").split(":")
            host = url_parts[0]
            port = int(url_parts[1]) if len(url_parts) > 1 else 8123
            
            self.client = clickhouse_connect.get_client(
                host=host,
                port=port,
                username="default",
                password="",
                database="default",
                send_receive_timeout=60,
                compress=True,
            )
            
            # Test connection
            result = self.client.query("SELECT 1")
            logger.info(f"Connected to ClickHouse at {host}:{port}")
            return self.client
            
        except Exception as e:
            logger.error(f"Failed to connect to ClickHouse: {e}")
            raise
    
    async def create_tables(self):
        """Create ClickHouse tables for analytics."""
        tables = {
            "cost_analytics": """
                CREATE TABLE IF NOT EXISTS cost_analytics (
                    timestamp DateTime64(3) DEFAULT now64(),
                    date Date DEFAULT toDate(timestamp),
                    
                    -- Provider and model
                    provider LowCardinality(String),
                    model_name LowCardinality(String),
                    endpoint String,
                    
                    -- Context
                    user_id String,
                    project_id String,
                    session_id String,
                    
                    -- Metrics
                    duration_ms Float64,
                    success UInt8,
                    
                    -- Token usage
                    input_tokens UInt32,
                    output_tokens UInt32,
                    total_tokens UInt32,
                    
                    -- Costs
                    input_cost Decimal(15,6),
                    output_cost Decimal(15,6),
                    total_cost Decimal(15,6),
                    currency LowCardinality(String) DEFAULT 'USD',
                    
                    -- Pricing
                    input_price_per_token Decimal(15,10),
                    output_price_per_token Decimal(15,10)
                ) ENGINE = MergeTree()
                PARTITION BY toYYYYMM(date)
                ORDER BY (timestamp, provider, model_name, user_id)
                TTL timestamp + INTERVAL 2 YEAR
                SETTINGS index_granularity = 8192;
            """,
            
            "usage_analytics": """
                CREATE TABLE IF NOT EXISTS usage_analytics (
                    timestamp DateTime64(3) DEFAULT now64(),
                    date Date DEFAULT toDate(timestamp),
                    hour UInt8 DEFAULT toHour(timestamp),
                    
                    -- Provider and model
                    provider LowCardinality(String),
                    model_name LowCardinality(String),
                    endpoint String,
                    
                    -- Context
                    user_id String,
                    project_id String,
                    
                    -- Usage metrics
                    request_count UInt32 DEFAULT 1,
                    token_count UInt32,
                    success_count UInt32,
                    error_count UInt32,
                    
                    -- Performance metrics
                    total_duration_ms Float64,
                    min_duration_ms Float64,
                    max_duration_ms Float64,
                    
                    -- Cost metrics
                    total_cost Decimal(15,6),
                    min_cost Decimal(15,6),
                    max_cost Decimal(15,6)
                ) ENGINE = SummingMergeTree()
                PARTITION BY toYYYYMM(date)
                ORDER BY (date, hour, provider, model_name, user_id, project_id)
                TTL timestamp + INTERVAL 1 YEAR
                SETTINGS index_granularity = 8192;
            """,
            
            "error_analytics": """
                CREATE TABLE IF NOT EXISTS error_analytics (
                    timestamp DateTime64(3) DEFAULT now64(),
                    date Date DEFAULT toDate(timestamp),
                    
                    -- Error details
                    severity LowCardinality(String),
                    category LowCardinality(String),
                    error_code LowCardinality(String),
                    
                    -- Provider and model
                    provider LowCardinality(String),
                    model_name LowCardinality(String),
                    endpoint String,
                    
                    -- Context
                    user_id String,
                    project_id String,
                    
                    -- Metrics
                    error_count UInt32 DEFAULT 1,
                    resolved UInt8 DEFAULT 0,
                    resolution_time_hours Float64
                ) ENGINE = SummingMergeTree()
                PARTITION BY toYYYYMM(date)
                ORDER BY (date, severity, category, provider, model_name)
                TTL timestamp + INTERVAL 2 YEAR
                SETTINGS index_granularity = 8192;
            """
        }
        
        for table_name, sql in tables.items():
            try:
                self.client.command(sql)
                logger.info(f"Created ClickHouse table: {table_name}")
            except Exception as e:
                logger.error(f"Failed to create ClickHouse table {table_name}: {e}")
                raise
    
    async def insert_batch(self, table: str, data: List[Dict[str, Any]]):
        """Insert batch data into ClickHouse."""
        if not data:
            return
            
        try:
            # Convert data to ClickHouse format
            columns = list(data[0].keys())
            rows = []
            for row in data:
                rows.append([row.get(col) for col in columns])
            
            self.client.insert(table, rows, column_names=columns)
            logger.debug(f"Inserted {len(data)} rows into {table}")
            
        except Exception as e:
            logger.error(f"Failed to insert batch into {table}: {e}")
            raise
    
    async def insert_cost_data(self, transaction_data: Dict[str, Any]):
        """Insert cost transaction data."""
        cost_row = {
            'timestamp': transaction_data.get('timestamp', datetime.utcnow()),
            'provider': transaction_data.get('provider'),
            'model_name': transaction_data.get('model_name'),
            'endpoint': transaction_data.get('endpoint'),
            'user_id': transaction_data.get('user_id'),
            'project_id': transaction_data.get('project_id'),
            'session_id': transaction_data.get('session_id'),
            'duration_ms': transaction_data.get('duration_ms'),
            'success': 1 if transaction_data.get('success') else 0,
            'input_tokens': transaction_data.get('token_usage', {}).get('input_tokens', 0),
            'output_tokens': transaction_data.get('token_usage', {}).get('output_tokens', 0),
            'total_tokens': transaction_data.get('token_usage', {}).get('total_tokens', 0),
            'input_cost': transaction_data.get('cost_breakdown', {}).get('input_cost', 0),
            'output_cost': transaction_data.get('cost_breakdown', {}).get('output_cost', 0),
            'total_cost': transaction_data.get('cost_breakdown', {}).get('total_cost', 0),
            'currency': transaction_data.get('cost_breakdown', {}).get('currency', 'USD'),
            'input_price_per_token': transaction_data.get('cost_breakdown', {}).get('input_price_per_token'),
            'output_price_per_token': transaction_data.get('cost_breakdown', {}).get('output_price_per_token'),
        }
        
        await self.insert_batch('cost_analytics', [cost_row])
    
    async def query_cost_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        provider: Optional[str] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Query cost summary with aggregation."""
        where_conditions = []
        
        if start_date:
            where_conditions.append(f"timestamp >= '{start_date.isoformat()}'")
        if end_date:
            where_conditions.append(f"timestamp <= '{end_date.isoformat()}'")
        if provider:
            where_conditions.append(f"provider = '{provider}'")
        if user_id:
            where_conditions.append(f"user_id = '{user_id}'")
        if project_id:
            where_conditions.append(f"project_id = '{project_id}'")
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        query = f"""
        SELECT
            sum(total_cost) as total_cost,
            count(*) as total_transactions,
            sum(input_tokens) as total_input_tokens,
            sum(output_tokens) as total_output_tokens,
            sum(total_tokens) as total_tokens,
            avg(duration_ms) as avg_duration_ms,
            sum(success) / count(*) as success_rate,
            uniqExact(user_id) as unique_users,
            uniqExact(project_id) as unique_projects
        FROM cost_analytics
        WHERE {where_clause}
        """
        
        result = self.client.query(query)
        if result.result_rows:
            row = result.result_rows[0]
            return {
                'total_cost': float(row[0]) if row[0] else 0,
                'total_transactions': int(row[1]),
                'total_input_tokens': int(row[2]),
                'total_output_tokens': int(row[3]),
                'total_tokens': int(row[4]),
                'avg_duration_ms': float(row[5]) if row[5] else 0,
                'success_rate': float(row[6]) if row[6] else 0,
                'unique_users': int(row[7]),
                'unique_projects': int(row[8]),
            }
        return {}
    
    async def query_cost_breakdown(
        self,
        group_by: str = 'provider',
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Query cost breakdown by specified dimension."""
        where_conditions = []
        
        if start_date:
            where_conditions.append(f"timestamp >= '{start_date.isoformat()}'")
        if end_date:
            where_conditions.append(f"timestamp <= '{end_date.isoformat()}'")
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        valid_group_by = ['provider', 'model_name', 'user_id', 'project_id', 'date']
        if group_by not in valid_group_by:
            group_by = 'provider'
        
        query = f"""
        SELECT
            {group_by},
            sum(total_cost) as total_cost,
            count(*) as transaction_count,
            sum(total_tokens) as total_tokens,
            avg(duration_ms) as avg_duration_ms
        FROM cost_analytics
        WHERE {where_clause}
        GROUP BY {group_by}
        ORDER BY total_cost DESC
        LIMIT 100
        """
        
        result = self.client.query(query)
        breakdown = []
        for row in result.result_rows:
            breakdown.append({
                group_by: row[0],
                'total_cost': float(row[1]) if row[1] else 0,
                'transaction_count': int(row[2]),
                'total_tokens': int(row[3]),
                'avg_duration_ms': float(row[4]) if row[4] else 0,
            })
        
        return breakdown
    
    async def close(self):
        """Close ClickHouse connection."""
        if self.client:
            self.client.close()
            logger.info("Closed ClickHouse connection")


# Global ClickHouse client instance
clickhouse_client = ClickHouseClient()


async def init_clickhouse():
    """Initialize ClickHouse connection and tables."""
    global _clickhouse_client
    
    try:
        _clickhouse_client = await clickhouse_client.connect()
        await clickhouse_client.create_tables()
        logger.info("ClickHouse client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize ClickHouse: {e}")
        raise


async def close_clickhouse():
    """Close ClickHouse connection."""
    await clickhouse_client.close()


def get_clickhouse_client() -> ClickHouseClient:
    """Get ClickHouse client instance."""
    if not _clickhouse_client:
        raise RuntimeError("ClickHouse client not initialized")
    return clickhouse_client