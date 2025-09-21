"""Transaction and cost tracking data models."""

from datetime import datetime
from typing import Dict, Any, Optional, List
from decimal import Decimal

from pydantic import BaseModel, Field, validator

from reskpoints.models.enums import AIProvider


class TokenUsage(BaseModel):
    """Token usage tracking."""
    
    input_tokens: int = Field(default=0, description="Number of input tokens")
    output_tokens: int = Field(default=0, description="Number of output tokens")
    total_tokens: int = Field(default=0, description="Total tokens used")
    
    @validator('total_tokens', always=True)
    def calculate_total_tokens(cls, v, values):
        """Calculate total tokens if not provided."""
        if v == 0:
            return values.get('input_tokens', 0) + values.get('output_tokens', 0)
        return v


class CostBreakdown(BaseModel):
    """Detailed cost breakdown."""
    
    input_cost: Decimal = Field(default=Decimal('0'), description="Cost for input tokens")
    output_cost: Decimal = Field(default=Decimal('0'), description="Cost for output tokens")
    base_cost: Decimal = Field(default=Decimal('0'), description="Base API call cost")
    additional_fees: Decimal = Field(default=Decimal('0'), description="Additional fees")
    total_cost: Decimal = Field(default=Decimal('0'), description="Total cost")
    currency: str = Field(default="USD", description="Currency code")
    
    # Pricing information
    input_price_per_token: Optional[Decimal] = Field(None, description="Price per input token")
    output_price_per_token: Optional[Decimal] = Field(None, description="Price per output token")
    
    @validator('total_cost', always=True)
    def calculate_total_cost(cls, v, values):
        """Calculate total cost if not provided."""
        if v == Decimal('0'):
            return (
                values.get('input_cost', Decimal('0')) +
                values.get('output_cost', Decimal('0')) +
                values.get('base_cost', Decimal('0')) +
                values.get('additional_fees', Decimal('0'))
            )
        return v
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
        }


class Transaction(BaseModel):
    """AI transaction tracking."""
    
    id: Optional[str] = Field(None, description="Unique transaction identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Transaction timestamp")
    
    # Provider and model information
    provider: AIProvider = Field(..., description="AI service provider")
    model_name: str = Field(..., description="AI model name")
    endpoint: str = Field(..., description="API endpoint")
    
    # Request information
    user_id: Optional[str] = Field(None, description="User identifier")
    project_id: Optional[str] = Field(None, description="Project identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    request_id: Optional[str] = Field(None, description="Request identifier")
    
    # Performance metrics
    duration_ms: Optional[float] = Field(None, description="Request duration in milliseconds")
    status_code: Optional[int] = Field(None, description="HTTP status code")
    success: bool = Field(default=True, description="Whether transaction was successful")
    
    # Token usage
    token_usage: Optional[TokenUsage] = Field(None, description="Token usage details")
    
    # Cost information
    cost_breakdown: Optional[CostBreakdown] = Field(None, description="Cost breakdown")
    
    # Content information (optional, for analysis)
    input_length: Optional[int] = Field(None, description="Input content length")
    output_length: Optional[int] = Field(None, description="Output content length")
    
    # Error information
    error_message: Optional[str] = Field(None, description="Error message if failed")
    error_code: Optional[str] = Field(None, description="Error code if failed")
    
    # Custom tags and metadata
    tags: Dict[str, str] = Field(default_factory=dict, description="Custom tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v),
        }


class CostSummary(BaseModel):
    """Cost summary for a time period."""
    
    period_start: datetime = Field(..., description="Period start time")
    period_end: datetime = Field(..., description="Period end time")
    
    # Aggregated costs
    total_cost: Decimal = Field(default=Decimal('0'), description="Total cost")
    total_transactions: int = Field(default=0, description="Total number of transactions")
    
    # Cost by provider
    cost_by_provider: Dict[str, Decimal] = Field(
        default_factory=dict,
        description="Cost breakdown by provider"
    )
    
    # Cost by model
    cost_by_model: Dict[str, Decimal] = Field(
        default_factory=dict,
        description="Cost breakdown by model"
    )
    
    # Cost by user/project
    cost_by_user: Dict[str, Decimal] = Field(
        default_factory=dict,
        description="Cost breakdown by user"
    )
    cost_by_project: Dict[str, Decimal] = Field(
        default_factory=dict,
        description="Cost breakdown by project"
    )
    
    # Token usage summary
    total_input_tokens: int = Field(default=0, description="Total input tokens")
    total_output_tokens: int = Field(default=0, description="Total output tokens")
    total_tokens: int = Field(default=0, description="Total tokens")
    
    # Performance summary
    avg_duration_ms: Optional[float] = Field(None, description="Average request duration")
    success_rate: Optional[float] = Field(None, description="Success rate percentage")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v),
        }


class BudgetAlert(BaseModel):
    """Budget monitoring and alerts."""
    
    id: Optional[str] = Field(None, description="Unique alert identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Alert timestamp")
    
    # Budget information
    budget_name: str = Field(..., description="Budget name")
    budget_limit: Decimal = Field(..., description="Budget limit")
    current_spend: Decimal = Field(..., description="Current spend")
    threshold_percentage: float = Field(..., description="Alert threshold percentage")
    
    # Scope
    user_id: Optional[str] = Field(None, description="User ID (if user-specific)")
    project_id: Optional[str] = Field(None, description="Project ID (if project-specific)")
    provider: Optional[AIProvider] = Field(None, description="Provider (if provider-specific)")
    
    # Alert details
    alert_triggered: bool = Field(default=False, description="Whether alert was triggered")
    alert_message: str = Field(..., description="Alert message")
    
    # Time period
    period_start: datetime = Field(..., description="Budget period start")
    period_end: datetime = Field(..., description="Budget period end")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v),
        }