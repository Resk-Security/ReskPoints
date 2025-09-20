"""Database schema and migration scripts for ReskPoints."""

# TimescaleDB schemas for metrics storage
TIMESCALE_SCHEMAS = {
    "ai_metrics": """
        CREATE TABLE IF NOT EXISTS ai_metrics (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            metric_type VARCHAR(50) NOT NULL,
            value DOUBLE PRECISION NOT NULL,
            unit VARCHAR(20) NOT NULL,
            
            -- Provider information
            provider VARCHAR(50) NOT NULL,
            model_name VARCHAR(100) NOT NULL,
            model_size VARCHAR(20),
            endpoint VARCHAR(200) NOT NULL,
            
            -- Context information
            user_id VARCHAR(100),
            project_id VARCHAR(100),
            session_id VARCHAR(100),
            request_id VARCHAR(100),
            
            -- Custom data
            tags JSONB DEFAULT '{}',
            metadata JSONB DEFAULT '{}',
            
            -- Indexes
            INDEX ai_metrics_timestamp_idx (timestamp DESC),
            INDEX ai_metrics_provider_idx (provider),
            INDEX ai_metrics_model_idx (model_name),
            INDEX ai_metrics_type_idx (metric_type),
            INDEX ai_metrics_user_idx (user_id),
            INDEX ai_metrics_project_idx (project_id)
        );
        
        -- Create hypertable for time-series optimization
        SELECT create_hypertable('ai_metrics', 'timestamp', if_not_exists => TRUE);
        
        -- Create retention policy (keep data for 1 year)
        SELECT add_retention_policy('ai_metrics', INTERVAL '1 year', if_not_exists => TRUE);
    """,
    
    "ai_errors": """
        CREATE TABLE IF NOT EXISTS ai_errors (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            severity VARCHAR(20) NOT NULL,
            category VARCHAR(50) NOT NULL,
            
            -- Error details
            message TEXT NOT NULL,
            code VARCHAR(100),
            details JSONB DEFAULT '{}',
            
            -- Provider information
            provider VARCHAR(50) NOT NULL,
            model_name VARCHAR(100) NOT NULL,
            endpoint VARCHAR(200) NOT NULL,
            
            -- Context information
            user_id VARCHAR(100),
            project_id VARCHAR(100),
            session_id VARCHAR(100),
            request_id VARCHAR(100),
            
            -- Debug information
            stack_trace TEXT,
            correlation_id VARCHAR(100),
            
            -- Resolution tracking
            resolved BOOLEAN DEFAULT FALSE,
            resolution_notes TEXT,
            resolved_at TIMESTAMPTZ,
            
            -- Custom data
            tags JSONB DEFAULT '{}',
            metadata JSONB DEFAULT '{}',
            
            -- Indexes
            INDEX ai_errors_timestamp_idx (timestamp DESC),
            INDEX ai_errors_severity_idx (severity),
            INDEX ai_errors_category_idx (category),
            INDEX ai_errors_provider_idx (provider),
            INDEX ai_errors_resolved_idx (resolved),
            INDEX ai_errors_user_idx (user_id),
            INDEX ai_errors_project_idx (project_id)
        );
        
        -- Create hypertable for time-series optimization
        SELECT create_hypertable('ai_errors', 'timestamp', if_not_exists => TRUE);
        
        -- Create retention policy (keep data for 2 years)
        SELECT add_retention_policy('ai_errors', INTERVAL '2 years', if_not_exists => TRUE);
    """,
    
    "model_metrics_summary": """
        CREATE TABLE IF NOT EXISTS model_metrics_summary (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            provider VARCHAR(50) NOT NULL,
            model_name VARCHAR(100) NOT NULL,
            time_window_start TIMESTAMPTZ NOT NULL,
            time_window_end TIMESTAMPTZ NOT NULL,
            
            -- Performance metrics
            total_requests INTEGER DEFAULT 0,
            successful_requests INTEGER DEFAULT 0,
            failed_requests INTEGER DEFAULT 0,
            
            -- Latency metrics
            avg_latency_ms DOUBLE PRECISION,
            p50_latency_ms DOUBLE PRECISION,
            p95_latency_ms DOUBLE PRECISION,
            p99_latency_ms DOUBLE PRECISION,
            
            -- Throughput metrics
            requests_per_second DOUBLE PRECISION,
            tokens_per_second DOUBLE PRECISION,
            
            -- Error metrics
            error_rate DOUBLE PRECISION,
            
            -- Cost metrics
            total_cost_usd DECIMAL(15,6),
            avg_cost_per_request DECIMAL(15,6),
            
            -- Token metrics
            total_tokens INTEGER,
            avg_tokens_per_request DOUBLE PRECISION,
            
            created_at TIMESTAMPTZ DEFAULT NOW(),
            
            -- Indexes
            INDEX model_metrics_provider_model_idx (provider, model_name),
            INDEX model_metrics_time_window_idx (time_window_start, time_window_end),
            UNIQUE INDEX model_metrics_unique_idx (provider, model_name, time_window_start, time_window_end)
        );
        
        -- Create hypertable for time-series optimization
        SELECT create_hypertable('model_metrics_summary', 'time_window_start', if_not_exists => TRUE);
    """
}

# PostgreSQL schemas for general data
POSTGRES_SCHEMAS = {
    "transactions": """
        CREATE TABLE IF NOT EXISTS transactions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            
            -- Provider and model information
            provider VARCHAR(50) NOT NULL,
            model_name VARCHAR(100) NOT NULL,
            endpoint VARCHAR(200) NOT NULL,
            
            -- Request information
            user_id VARCHAR(100),
            project_id VARCHAR(100),
            session_id VARCHAR(100),
            request_id VARCHAR(100),
            
            -- Performance metrics
            duration_ms DOUBLE PRECISION,
            status_code INTEGER,
            success BOOLEAN DEFAULT TRUE,
            
            -- Token usage
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            
            -- Cost information
            input_cost DECIMAL(15,6) DEFAULT 0,
            output_cost DECIMAL(15,6) DEFAULT 0,
            base_cost DECIMAL(15,6) DEFAULT 0,
            additional_fees DECIMAL(15,6) DEFAULT 0,
            total_cost DECIMAL(15,6) DEFAULT 0,
            currency VARCHAR(3) DEFAULT 'USD',
            
            -- Pricing information
            input_price_per_token DECIMAL(15,10),
            output_price_per_token DECIMAL(15,10),
            
            -- Content information
            input_length INTEGER,
            output_length INTEGER,
            
            -- Error information
            error_message TEXT,
            error_code VARCHAR(100),
            
            -- Custom data
            tags JSONB DEFAULT '{}',
            metadata JSONB DEFAULT '{}',
            
            -- Indexes
            INDEX transactions_timestamp_idx (timestamp DESC),
            INDEX transactions_provider_idx (provider),
            INDEX transactions_model_idx (model_name),
            INDEX transactions_user_idx (user_id),
            INDEX transactions_project_idx (project_id),
            INDEX transactions_success_idx (success)
        );
    """,
    
    "tickets": """
        CREATE TABLE IF NOT EXISTS tickets (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            
            -- Ticket details
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'open',
            priority VARCHAR(20) NOT NULL,
            category VARCHAR(50) NOT NULL,
            severity VARCHAR(20) NOT NULL,
            
            -- Assignment and tracking
            assignee_id VARCHAR(100),
            reporter_id VARCHAR(100),
            team VARCHAR(100),
            
            -- Context information
            provider VARCHAR(50),
            model_name VARCHAR(100),
            endpoint VARCHAR(200),
            user_id VARCHAR(100),
            project_id VARCHAR(100),
            
            -- Error tracking
            error_ids JSONB DEFAULT '[]',
            causality_node_ids JSONB DEFAULT '[]',
            
            -- Resolution tracking
            resolution_notes TEXT,
            resolved_at TIMESTAMPTZ,
            closed_at TIMESTAMPTZ,
            
            -- SLA tracking
            sla_deadline TIMESTAMPTZ,
            escalated BOOLEAN DEFAULT FALSE,
            escalated_at TIMESTAMPTZ,
            
            -- Custom data
            tags JSONB DEFAULT '{}',
            metadata JSONB DEFAULT '{}',
            
            -- Indexes
            INDEX tickets_status_idx (status),
            INDEX tickets_priority_idx (priority),
            INDEX tickets_severity_idx (severity),
            INDEX tickets_assignee_idx (assignee_id),
            INDEX tickets_created_at_idx (created_at DESC),
            INDEX tickets_provider_idx (provider)
        );
    """,
    
    "causality_nodes": """
        CREATE TABLE IF NOT EXISTS causality_nodes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            
            -- Node details
            event_type VARCHAR(100) NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            severity VARCHAR(20) NOT NULL,
            
            -- Context information
            provider VARCHAR(50),
            model_name VARCHAR(100),
            endpoint VARCHAR(200),
            component VARCHAR(100),
            
            -- Error information
            error_id UUID,
            metric_id UUID,
            
            -- Impact assessment
            impact_score DOUBLE PRECISION CHECK (impact_score >= 0 AND impact_score <= 1),
            affected_users INTEGER,
            affected_requests INTEGER,
            
            -- Resolution tracking
            resolved BOOLEAN DEFAULT FALSE,
            resolved_at TIMESTAMPTZ,
            root_cause TEXT,
            
            -- Custom data
            tags JSONB DEFAULT '{}',
            metadata JSONB DEFAULT '{}',
            
            -- Indexes
            INDEX causality_nodes_timestamp_idx (timestamp DESC),
            INDEX causality_nodes_event_type_idx (event_type),
            INDEX causality_nodes_severity_idx (severity),
            INDEX causality_nodes_resolved_idx (resolved),
            INDEX causality_nodes_provider_idx (provider)
        );
    """,
    
    "causality_edges": """
        CREATE TABLE IF NOT EXISTS causality_edges (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            
            -- Relationship details
            source_node_id UUID NOT NULL REFERENCES causality_nodes(id),
            target_node_id UUID NOT NULL REFERENCES causality_nodes(id),
            relationship_type VARCHAR(100) NOT NULL,
            
            -- Confidence and strength
            confidence DOUBLE PRECISION NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
            strength DOUBLE PRECISION NOT NULL CHECK (strength >= 0 AND strength <= 1),
            
            -- Evidence
            evidence JSONB DEFAULT '[]',
            correlation_score DOUBLE PRECISION,
            temporal_distance_ms DOUBLE PRECISION,
            
            -- Analysis details
            analysis_method VARCHAR(100) NOT NULL,
            validated BOOLEAN DEFAULT FALSE,
            validated_by VARCHAR(100),
            validated_at TIMESTAMPTZ,
            
            -- Custom data
            tags JSONB DEFAULT '{}',
            metadata JSONB DEFAULT '{}',
            
            -- Indexes
            INDEX causality_edges_source_idx (source_node_id),
            INDEX causality_edges_target_idx (target_node_id),
            INDEX causality_edges_relationship_idx (relationship_type),
            INDEX causality_edges_confidence_idx (confidence DESC),
            INDEX causality_edges_validated_idx (validated),
            UNIQUE INDEX causality_edges_unique_idx (source_node_id, target_node_id, relationship_type)
        );
    """
}


async def create_timescale_schemas(connection):
    """Create TimescaleDB schemas for metrics storage."""
    for table_name, schema in TIMESCALE_SCHEMAS.items():
        try:
            await connection.execute(schema)
            print(f"✅ Created TimescaleDB table: {table_name}")
        except Exception as e:
            print(f"❌ Failed to create TimescaleDB table {table_name}: {e}")
            raise


async def create_postgres_schemas(connection):
    """Create PostgreSQL schemas for general data."""
    for table_name, schema in POSTGRES_SCHEMAS.items():
        try:
            await connection.execute(schema)
            print(f"✅ Created PostgreSQL table: {table_name}")
        except Exception as e:
            print(f"❌ Failed to create PostgreSQL table {table_name}: {e}")
            raise


async def run_migrations():
    """Run all database migrations."""
    from reskpoints.infrastructure.database.connection import (
        get_postgres_connection,
        get_timescale_connection,
    )
    
    print("🚀 Running database migrations...")
    
    try:
        # Create PostgreSQL schemas
        async with get_postgres_connection() as pg_conn:
            await create_postgres_schemas(pg_conn)
        
        # Create TimescaleDB schemas
        async with get_timescale_connection() as ts_conn:
            await create_timescale_schemas(ts_conn)
        
        print("✅ All database migrations completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise