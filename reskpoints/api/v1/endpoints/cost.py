"""Cost tracking API endpoints."""

from typing import List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from reskpoints.models.cost import Transaction, CostSummary, BudgetAlert
from reskpoints.models.enums import AIProvider

router = APIRouter()


# Response models
class TransactionsResponse(BaseModel):
    """Transactions list response."""
    transactions: List[Transaction]
    total: int
    page: int
    per_page: int


class BudgetAlertsResponse(BaseModel):
    """Budget alerts list response."""
    alerts: List[BudgetAlert]
    total: int
    page: int
    per_page: int


class OptimizationRecommendations(BaseModel):
    """Cost optimization recommendations."""
    recommendations: List[dict]
    potential_total_savings: str
    analysis_period_days: int


@router.post("/transactions", response_model=Transaction)
async def submit_transaction(transaction: Transaction):
    """Submit a new transaction for cost tracking."""
    try:
        # Try to use cost tracker if available
        try:
            from reskpoints.services.cost.tracker import get_cost_tracker
            tracker = get_cost_tracker()
            success = await tracker.track_transaction(transaction)
            
            if not success:
                raise HTTPException(status_code=500, detail="Failed to track transaction")
        except ImportError:
            # Fallback if cost tracker not available
            pass
        
        # Generate ID for response
        transaction.id = f"txn_{datetime.utcnow().timestamp()}"
        return transaction
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tracking transaction: {e}")


@router.get("/transactions", response_model=TransactionsResponse)
async def list_transactions(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=1000, description="Items per page"),
    provider: Optional[AIProvider] = Query(None, description="Filter by provider"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    start_time: Optional[datetime] = Query(None, description="Start time filter"),
    end_time: Optional[datetime] = Query(None, description="End time filter"),
):
    """List transactions with filtering and pagination."""
    # TODO: Implement actual database query with new infrastructure
    return TransactionsResponse(
        transactions=[],
        total=0,
        page=page,
        per_page=per_page,
    )


@router.get("/transactions/{transaction_id}", response_model=Transaction)
async def get_transaction(transaction_id: str):
    """Get a specific transaction by ID."""
    # TODO: Implement transaction retrieval
    raise HTTPException(status_code=404, detail="Transaction not found")


@router.get("/summary", response_model=CostSummary)
async def get_cost_summary(
    start_time: Optional[datetime] = Query(None, description="Start time for summary"),
    end_time: Optional[datetime] = Query(None, description="End time for summary"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    provider: Optional[AIProvider] = Query(None, description="Filter by provider"),
):
    """Get cost summary for a time period."""
    try:
        # Try to use cost aggregator if available
        try:
            from reskpoints.services.cost.tracker import get_cost_aggregator
            aggregator = get_cost_aggregator()
            summary = await aggregator.get_cost_summary(
                start_date=start_time,
                end_date=end_time,
                user_id=user_id,
                project_id=project_id,
                provider=provider.value if provider else None,
            )
            return summary
        except ImportError:
            # Fallback if cost aggregator not available
            start = start_time or datetime.utcnow() - timedelta(days=30)
            end = end_time or datetime.utcnow()
            
            return CostSummary(
                period_start=start,
                period_end=end,
                total_cost=Decimal('0'),
                total_transactions=0,
                cost_by_provider={},
                cost_by_model={},
                cost_by_user={},
                cost_by_project={},
                total_input_tokens=0,
                total_output_tokens=0,
                total_tokens=0,
            )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cost summary: {e}")


@router.get("/budget/alerts", response_model=BudgetAlertsResponse)
async def list_budget_alerts(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=1000, description="Items per page"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    active_only: bool = Query(True, description="Show only active alerts"),
):
    """List budget alerts."""
    # TODO: Implement budget alert query with new infrastructure
    return BudgetAlertsResponse(
        alerts=[],
        total=0,
        page=page,
        per_page=per_page,
    )


@router.post("/budget/alerts", response_model=BudgetAlert)
async def create_budget_alert(alert: BudgetAlert):
    """Create a new budget alert."""
    try:
        # Try to use budget manager if available
        try:
            from reskpoints.services.cost.tracker import get_budget_manager
            manager = get_budget_manager()
            success = await manager.create_budget_alert(alert)
            
            if not success:
                raise HTTPException(status_code=500, detail="Failed to create budget alert")
        except ImportError:
            # Fallback if budget manager not available
            pass
        
        # Generate ID for response
        alert.id = f"alert_{datetime.utcnow().timestamp()}"
        return alert
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating budget alert: {e}")


@router.get("/optimization/recommendations", response_model=OptimizationRecommendations)
async def get_optimization_recommendations(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    days: int = Query(30, ge=1, le=365, description="Analysis period in days"),
):
    """Get cost optimization recommendations."""
    try:
        # Try to use cost optimizer if available
        try:
            from reskpoints.services.cost.tracker import get_cost_optimizer
            optimizer = get_cost_optimizer()
            recommendations = await optimizer.analyze_usage_patterns(
                user_id=user_id,
                project_id=project_id,
                days=days,
            )
        except ImportError:
            # Fallback recommendations if optimizer not available
            recommendations = [
                {
                    'type': 'fallback',
                    'recommendation': 'Install dependencies to enable advanced cost optimization',
                    'potential_savings': '0%',
                    'confidence': 1.0,
                }
            ]
        
        # Calculate potential total savings
        total_savings = sum(
            float(rec.get('potential_savings', '0%').replace('%', ''))
            for rec in recommendations
        )
        
        return OptimizationRecommendations(
            recommendations=recommendations,
            potential_total_savings=f"{total_savings:.1f}%",
            analysis_period_days=days,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {e}")