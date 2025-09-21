"""Cost tracking service with provider-specific pricing and optimization."""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass

from reskpoints.models.cost import Transaction, CostBreakdown, TokenUsage, CostSummary, BudgetAlert
from reskpoints.models.enums import AIProvider
from reskpoints.infrastructure.database.connection import get_postgres_connection
from reskpoints.infrastructure.database.clickhouse import get_clickhouse_client
from reskpoints.infrastructure.cache.redis import get_cache
from reskpoints.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ProviderPricing:
    """Provider-specific pricing configuration."""
    input_price_per_1k_tokens: Decimal
    output_price_per_1k_tokens: Decimal
    base_cost_per_request: Decimal = Decimal('0')
    currency: str = 'USD'


class CostTracker:
    """Cost tracker with provider-specific pricing models."""
    
    def __init__(self):
        # Pricing models for different providers (per 1K tokens)
        self.pricing_models: Dict[str, Dict[str, ProviderPricing]] = {
            AIProvider.OPENAI: {
                'gpt-4': ProviderPricing(Decimal('0.03'), Decimal('0.06')),
                'gpt-4-turbo': ProviderPricing(Decimal('0.01'), Decimal('0.03')),
                'gpt-3.5-turbo': ProviderPricing(Decimal('0.0015'), Decimal('0.002')),
                'gpt-3.5-turbo-16k': ProviderPricing(Decimal('0.003'), Decimal('0.004')),
            },
            AIProvider.ANTHROPIC: {
                'claude-3-opus': ProviderPricing(Decimal('0.015'), Decimal('0.075')),
                'claude-3-sonnet': ProviderPricing(Decimal('0.003'), Decimal('0.015')),
                'claude-3-haiku': ProviderPricing(Decimal('0.00025'), Decimal('0.00125')),
            },
            AIProvider.GOOGLE: {
                'gemini-pro': ProviderPricing(Decimal('0.0005'), Decimal('0.0015')),
                'gemini-pro-vision': ProviderPricing(Decimal('0.0005'), Decimal('0.0015')),
            },
            AIProvider.AZURE: {
                'gpt-4': ProviderPricing(Decimal('0.03'), Decimal('0.06')),
                'gpt-35-turbo': ProviderPricing(Decimal('0.0015'), Decimal('0.002')),
            },
        }
        
        # Dynamic pricing multipliers (for time-based pricing)
        self.pricing_multipliers: Dict[str, Decimal] = {}
        
    async def calculate_transaction_cost(
        self,
        provider: AIProvider,
        model_name: str,
        token_usage: TokenUsage,
        custom_pricing: Optional[ProviderPricing] = None,
    ) -> CostBreakdown:
        """Calculate cost for a transaction."""
        try:
            # Get pricing model
            pricing = custom_pricing
            if not pricing:
                provider_pricing = self.pricing_models.get(provider.value, {})
                pricing = provider_pricing.get(model_name)
                
                if not pricing:
                    logger.warning(f"No pricing model for {provider}/{model_name}, using default")
                    pricing = ProviderPricing(Decimal('0.001'), Decimal('0.002'))
            
            # Calculate costs
            input_cost = (Decimal(token_usage.input_tokens) / 1000) * pricing.input_price_per_1k_tokens
            output_cost = (Decimal(token_usage.output_tokens) / 1000) * pricing.output_price_per_1k_tokens
            base_cost = pricing.base_cost_per_request
            
            # Apply dynamic pricing multipliers if any
            multiplier_key = f"{provider.value}:{model_name}"
            multiplier = self.pricing_multipliers.get(multiplier_key, Decimal('1.0'))
            
            input_cost *= multiplier
            output_cost *= multiplier
            base_cost *= multiplier
            
            return CostBreakdown(
                input_cost=input_cost,
                output_cost=output_cost,
                base_cost=base_cost,
                additional_fees=Decimal('0'),
                total_cost=input_cost + output_cost + base_cost,
                currency=pricing.currency,
                input_price_per_token=pricing.input_price_per_1k_tokens / 1000,
                output_price_per_token=pricing.output_price_per_1k_tokens / 1000,
            )
            
        except Exception as e:
            logger.error(f"Error calculating transaction cost: {e}")
            return CostBreakdown()
    
    async def track_transaction(self, transaction: Transaction) -> bool:
        """Track a transaction with cost calculation."""
        try:
            # Calculate cost if not provided
            if not transaction.cost_breakdown and transaction.token_usage:
                transaction.cost_breakdown = await self.calculate_transaction_cost(
                    transaction.provider,
                    transaction.model_name,
                    transaction.token_usage,
                )
            
            # Store in PostgreSQL
            async with get_postgres_connection() as conn:
                await conn.execute("""
                    INSERT INTO transactions (
                        timestamp, provider, model_name, endpoint, user_id, project_id,
                        session_id, request_id, duration_ms, status_code, success,
                        input_tokens, output_tokens, total_tokens,
                        input_cost, output_cost, base_cost, additional_fees, total_cost, currency,
                        input_price_per_token, output_price_per_token,
                        input_length, output_length, error_message, error_code,
                        tags, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28)
                """, 
                    transaction.timestamp,
                    transaction.provider.value,
                    transaction.model_name,
                    transaction.endpoint,
                    transaction.user_id,
                    transaction.project_id,
                    transaction.session_id,
                    transaction.request_id,
                    transaction.duration_ms,
                    transaction.status_code,
                    transaction.success,
                    transaction.token_usage.input_tokens if transaction.token_usage else 0,
                    transaction.token_usage.output_tokens if transaction.token_usage else 0,
                    transaction.token_usage.total_tokens if transaction.token_usage else 0,
                    transaction.cost_breakdown.input_cost if transaction.cost_breakdown else Decimal('0'),
                    transaction.cost_breakdown.output_cost if transaction.cost_breakdown else Decimal('0'),
                    transaction.cost_breakdown.base_cost if transaction.cost_breakdown else Decimal('0'),
                    transaction.cost_breakdown.additional_fees if transaction.cost_breakdown else Decimal('0'),
                    transaction.cost_breakdown.total_cost if transaction.cost_breakdown else Decimal('0'),
                    transaction.cost_breakdown.currency if transaction.cost_breakdown else 'USD',
                    transaction.cost_breakdown.input_price_per_token if transaction.cost_breakdown else None,
                    transaction.cost_breakdown.output_price_per_token if transaction.cost_breakdown else None,
                    transaction.input_length,
                    transaction.output_length,
                    transaction.error_message,
                    transaction.error_code,
                    transaction.tags,
                    transaction.metadata,
                )
            
            # Store in ClickHouse for analytics
            clickhouse = get_clickhouse_client()
            await clickhouse.insert_cost_data(transaction.dict())
            
            # Update real-time usage tracking
            if transaction.user_id:
                await self._update_user_usage(transaction)
            
            return True
            
        except Exception as e:
            logger.error(f"Error tracking transaction: {e}")
            return False
    
    async def _update_user_usage(self, transaction: Transaction):
        """Update real-time user usage for quota tracking."""
        cache = get_cache()
        
        # Update token usage
        await cache.increment_usage(
            transaction.user_id,
            'tokens',
            transaction.token_usage.total_tokens if transaction.token_usage else 0,
        )
        
        # Update cost usage
        cost_cents = int((transaction.cost_breakdown.total_cost * 100)) if transaction.cost_breakdown else 0
        await cache.increment_usage(
            transaction.user_id,
            'cost_cents',
            cost_cents,
        )
        
        # Update request count
        await cache.increment_usage(
            transaction.user_id,
            'requests',
            1,
        )
    
    async def update_pricing(
        self,
        provider: AIProvider,
        model_name: str,
        pricing: ProviderPricing,
    ):
        """Update pricing for a provider/model combination."""
        if provider.value not in self.pricing_models:
            self.pricing_models[provider.value] = {}
        
        self.pricing_models[provider.value][model_name] = pricing
        logger.info(f"Updated pricing for {provider.value}/{model_name}")
    
    async def set_pricing_multiplier(
        self,
        provider: AIProvider,
        model_name: str,
        multiplier: Decimal,
    ):
        """Set dynamic pricing multiplier for surge pricing."""
        key = f"{provider.value}:{model_name}"
        self.pricing_multipliers[key] = multiplier
        logger.info(f"Set pricing multiplier {multiplier} for {key}")


class CostAggregator:
    """Cost aggregation and reporting service."""
    
    async def get_cost_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> CostSummary:
        """Get cost summary with aggregation."""
        try:
            # Check cache first
            cache = get_cache()
            time_range = f"{start_date.isoformat() if start_date else 'none'}_{end_date.isoformat() if end_date else 'none'}"
            cached_summary = await cache.get_cost_summary(user_id, project_id, provider, time_range)
            if cached_summary:
                return CostSummary(**cached_summary)
            
            # Default time range
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            # Query from ClickHouse for fast aggregation
            clickhouse = get_clickhouse_client()
            summary_data = await clickhouse.query_cost_summary(
                start_date=start_date,
                end_date=end_date,
                provider=provider,
                user_id=user_id,
                project_id=project_id,
            )
            
            # Get breakdown data
            provider_breakdown = await clickhouse.query_cost_breakdown('provider', start_date, end_date)
            model_breakdown = await clickhouse.query_cost_breakdown('model_name', start_date, end_date)
            user_breakdown = await clickhouse.query_cost_breakdown('user_id', start_date, end_date)
            project_breakdown = await clickhouse.query_cost_breakdown('project_id', start_date, end_date)
            
            # Build cost summary
            cost_summary = CostSummary(
                period_start=start_date,
                period_end=end_date,
                total_cost=Decimal(str(summary_data.get('total_cost', 0))),
                total_transactions=summary_data.get('total_transactions', 0),
                cost_by_provider={item['provider']: Decimal(str(item['total_cost'])) for item in provider_breakdown},
                cost_by_model={item['model_name']: Decimal(str(item['total_cost'])) for item in model_breakdown},
                cost_by_user={item['user_id']: Decimal(str(item['total_cost'])) for item in user_breakdown if item['user_id']},
                cost_by_project={item['project_id']: Decimal(str(item['total_cost'])) for item in project_breakdown if item['project_id']},
                total_input_tokens=summary_data.get('total_input_tokens', 0),
                total_output_tokens=summary_data.get('total_output_tokens', 0),
                total_tokens=summary_data.get('total_tokens', 0),
                avg_duration_ms=summary_data.get('avg_duration_ms'),
                success_rate=summary_data.get('success_rate'),
            )
            
            # Cache the result
            await cache.cache_cost_summary(user_id, project_id, provider, time_range, cost_summary.dict(), ttl=600)
            
            return cost_summary
            
        except Exception as e:
            logger.error(f"Error getting cost summary: {e}")
            return CostSummary(
                period_start=start_date or datetime.utcnow(),
                period_end=end_date or datetime.utcnow(),
            )


class BudgetManager:
    """Budget monitoring and alert management."""
    
    def __init__(self):
        self.budget_alerts: Dict[str, BudgetAlert] = {}
    
    async def create_budget_alert(self, alert: BudgetAlert) -> bool:
        """Create a new budget alert."""
        try:
            async with get_postgres_connection() as conn:
                await conn.execute("""
                    INSERT INTO budget_alerts (
                        budget_name, budget_limit, threshold_percentage,
                        user_id, project_id, provider, period_start, period_end,
                        alert_message
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                    alert.budget_name,
                    alert.budget_limit,
                    alert.threshold_percentage,
                    alert.user_id,
                    alert.project_id,
                    alert.provider.value if alert.provider else None,
                    alert.period_start,
                    alert.period_end,
                    alert.alert_message,
                )
            
            # Store in memory for fast checking
            alert_key = self._get_alert_key(alert)
            self.budget_alerts[alert_key] = alert
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating budget alert: {e}")
            return False
    
    async def check_budget_alerts(self):
        """Check all budget alerts and trigger if necessary."""
        for alert_key, alert in self.budget_alerts.items():
            try:
                # Get current spend
                aggregator = CostAggregator()
                summary = await aggregator.get_cost_summary(
                    start_date=alert.period_start,
                    end_date=alert.period_end,
                    user_id=alert.user_id,
                    project_id=alert.project_id,
                    provider=alert.provider.value if alert.provider else None,
                )
                
                current_spend = summary.total_cost
                spend_percentage = (current_spend / alert.budget_limit) * 100
                
                # Check if alert should be triggered
                if spend_percentage >= alert.threshold_percentage and not alert.alert_triggered:
                    await self._trigger_budget_alert(alert, current_spend, spend_percentage)
                
            except Exception as e:
                logger.error(f"Error checking budget alert {alert_key}: {e}")
    
    async def _trigger_budget_alert(self, alert: BudgetAlert, current_spend: Decimal, spend_percentage: float):
        """Trigger a budget alert."""
        alert.alert_triggered = True
        alert.current_spend = current_spend
        
        logger.warning(f"Budget alert triggered: {alert.budget_name} - {spend_percentage:.1f}% of budget used")
        
        # TODO: Send actual alerts (email, Slack, webhook)
        # For now, just log the alert
        
        # Update alert in database
        try:
            async with get_postgres_connection() as conn:
                await conn.execute("""
                    UPDATE budget_alerts 
                    SET alert_triggered = TRUE, current_spend = $2, updated_at = NOW()
                    WHERE budget_name = $1
                """, alert.budget_name, current_spend)
        except Exception as e:
            logger.error(f"Error updating budget alert: {e}")
    
    def _get_alert_key(self, alert: BudgetAlert) -> str:
        """Generate unique key for budget alert."""
        parts = [alert.budget_name]
        if alert.user_id:
            parts.append(f"user:{alert.user_id}")
        if alert.project_id:
            parts.append(f"project:{alert.project_id}")
        if alert.provider:
            parts.append(f"provider:{alert.provider.value}")
        
        return ":".join(parts)


class CostOptimizer:
    """Cost optimization recommendations engine."""
    
    async def analyze_usage_patterns(
        self,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """Analyze usage patterns for optimization opportunities."""
        try:
            recommendations = []
            
            # Get usage data
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            clickhouse = get_clickhouse_client()
            
            # Analyze model efficiency
            efficiency_data = await self._analyze_model_efficiency(clickhouse, start_date, end_date, user_id, project_id)
            recommendations.extend(efficiency_data)
            
            # Analyze token usage patterns
            token_patterns = await self._analyze_token_patterns(clickhouse, start_date, end_date, user_id, project_id)
            recommendations.extend(token_patterns)
            
            # Analyze error rates and costs
            error_costs = await self._analyze_error_costs(clickhouse, start_date, end_date, user_id, project_id)
            recommendations.extend(error_costs)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error analyzing usage patterns: {e}")
            return []
    
    async def _analyze_model_efficiency(self, clickhouse, start_date, end_date, user_id, project_id):
        """Analyze model cost efficiency."""
        # TODO: Implement model efficiency analysis
        return [
            {
                'type': 'model_efficiency',
                'recommendation': 'Consider using gpt-3.5-turbo for simple tasks instead of gpt-4',
                'potential_savings': '40%',
                'confidence': 0.8,
            }
        ]
    
    async def _analyze_token_patterns(self, clickhouse, start_date, end_date, user_id, project_id):
        """Analyze token usage patterns."""
        # TODO: Implement token pattern analysis
        return [
            {
                'type': 'token_optimization',
                'recommendation': 'Optimize prompts to reduce input token usage',
                'potential_savings': '15%',
                'confidence': 0.7,
            }
        ]
    
    async def _analyze_error_costs(self, clickhouse, start_date, end_date, user_id, project_id):
        """Analyze costs related to errors and retries."""
        # TODO: Implement error cost analysis
        return [
            {
                'type': 'error_reduction',
                'recommendation': 'Implement better error handling to reduce retry costs',
                'potential_savings': '10%',
                'confidence': 0.9,
            }
        ]


# Global service instances
cost_tracker = CostTracker()
cost_aggregator = CostAggregator()
budget_manager = BudgetManager()
cost_optimizer = CostOptimizer()


def get_cost_tracker() -> CostTracker:
    """Get the global cost tracker instance."""
    return cost_tracker


def get_cost_aggregator() -> CostAggregator:
    """Get the global cost aggregator instance."""
    return cost_aggregator


def get_budget_manager() -> BudgetManager:
    """Get the global budget manager instance."""
    return budget_manager


def get_cost_optimizer() -> CostOptimizer:
    """Get the global cost optimizer instance."""
    return cost_optimizer