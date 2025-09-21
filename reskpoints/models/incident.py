"""Incident management data models."""

from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum

from pydantic import BaseModel, Field, validator

from reskpoints.models.enums import ErrorSeverity, AIProvider


class TicketStatus(str, Enum):
    """Ticket status workflow."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"


class TicketPriority(str, Enum):
    """Ticket priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TicketCategory(str, Enum):
    """Ticket categories."""
    BUG = "bug"
    PERFORMANCE = "performance"
    SECURITY = "security"
    COST_OPTIMIZATION = "cost_optimization"
    QUOTA_MANAGEMENT = "quota_management"
    INTEGRATION_ISSUE = "integration_issue"
    OTHER = "other"


class Ticket(BaseModel):
    """Incident ticket data model."""
    
    id: Optional[str] = Field(None, description="Unique ticket identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    # Ticket details
    title: str = Field(..., description="Ticket title")
    description: str = Field(..., description="Ticket description")
    status: TicketStatus = Field(default=TicketStatus.OPEN, description="Ticket status")
    priority: TicketPriority = Field(..., description="Ticket priority")
    category: TicketCategory = Field(..., description="Ticket category")
    severity: ErrorSeverity = Field(..., description="Error severity")
    
    # Assignment and tracking
    assignee_id: Optional[str] = Field(None, description="Assigned user ID")
    reporter_id: Optional[str] = Field(None, description="Reporter user ID")
    team: Optional[str] = Field(None, description="Assigned team")
    
    # Context information
    provider: Optional[AIProvider] = Field(None, description="Related AI provider")
    model_name: Optional[str] = Field(None, description="Related AI model")
    endpoint: Optional[str] = Field(None, description="Related API endpoint")
    user_id: Optional[str] = Field(None, description="Affected user ID")
    project_id: Optional[str] = Field(None, description="Affected project ID")
    
    # Error tracking
    error_ids: List[str] = Field(default_factory=list, description="Related error IDs")
    causality_node_ids: List[str] = Field(default_factory=list, description="Related causality nodes")
    
    # Resolution tracking
    resolution_notes: Optional[str] = Field(None, description="Resolution notes")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")
    closed_at: Optional[datetime] = Field(None, description="Closure timestamp")
    
    # SLA tracking
    sla_deadline: Optional[datetime] = Field(None, description="SLA deadline")
    escalated: bool = Field(default=False, description="Whether ticket was escalated")
    escalated_at: Optional[datetime] = Field(None, description="Escalation timestamp")
    
    # Custom tags and metadata
    tags: Dict[str, str] = Field(default_factory=dict, description="Custom tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class CausalityNode(BaseModel):
    """Node in the causality graph representing an error or event."""
    
    id: Optional[str] = Field(None, description="Unique node identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Node timestamp")
    
    # Node details
    event_type: str = Field(..., description="Type of event (error, metric_anomaly, etc.)")
    title: str = Field(..., description="Node title")
    description: str = Field(..., description="Node description")
    severity: ErrorSeverity = Field(..., description="Event severity")
    
    # Context information
    provider: Optional[AIProvider] = Field(None, description="Related AI provider")
    model_name: Optional[str] = Field(None, description="Related AI model")
    endpoint: Optional[str] = Field(None, description="Related API endpoint")
    component: Optional[str] = Field(None, description="System component")
    
    # Error information
    error_id: Optional[str] = Field(None, description="Related error ID")
    metric_id: Optional[str] = Field(None, description="Related metric ID")
    
    # Impact assessment
    impact_score: Optional[float] = Field(None, description="Impact score (0-1)")
    affected_users: Optional[int] = Field(None, description="Number of affected users")
    affected_requests: Optional[int] = Field(None, description="Number of affected requests")
    
    # Resolution tracking
    resolved: bool = Field(default=False, description="Whether event is resolved")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")
    root_cause: Optional[str] = Field(None, description="Root cause description")
    
    # Custom tags and metadata
    tags: Dict[str, str] = Field(default_factory=dict, description="Custom tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class CausalityEdge(BaseModel):
    """Edge in the causality graph representing a relationship between events."""
    
    id: Optional[str] = Field(None, description="Unique edge identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Edge creation timestamp")
    
    # Relationship details
    source_node_id: str = Field(..., description="Source node ID")
    target_node_id: str = Field(..., description="Target node ID")
    relationship_type: str = Field(..., description="Type of relationship (causes, correlates, etc.)")
    
    # Confidence and strength
    confidence: float = Field(..., description="Confidence in the relationship (0-1)")
    strength: float = Field(..., description="Strength of the relationship (0-1)")
    
    # Evidence
    evidence: List[str] = Field(default_factory=list, description="Evidence supporting the relationship")
    correlation_score: Optional[float] = Field(None, description="Statistical correlation score")
    temporal_distance_ms: Optional[float] = Field(None, description="Time distance in milliseconds")
    
    # Analysis details
    analysis_method: str = Field(..., description="Method used to determine relationship")
    validated: bool = Field(default=False, description="Whether relationship is validated")
    validated_by: Optional[str] = Field(None, description="Who validated the relationship")
    validated_at: Optional[datetime] = Field(None, description="Validation timestamp")
    
    # Custom tags and metadata
    tags: Dict[str, str] = Field(default_factory=dict, description="Custom tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('confidence', 'strength')
    def validate_scores(cls, v):
        """Validate score values are between 0 and 1."""
        if v < 0 or v > 1:
            raise ValueError("Score must be between 0 and 1")
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class IncidentReport(BaseModel):
    """Comprehensive incident report."""
    
    id: Optional[str] = Field(None, description="Unique report identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Report creation timestamp")
    
    # Incident details
    title: str = Field(..., description="Incident title")
    summary: str = Field(..., description="Incident summary")
    start_time: datetime = Field(..., description="Incident start time")
    end_time: Optional[datetime] = Field(None, description="Incident end time")
    duration_minutes: Optional[float] = Field(None, description="Incident duration in minutes")
    
    # Impact assessment
    severity: ErrorSeverity = Field(..., description="Incident severity")
    affected_users: Optional[int] = Field(None, description="Number of affected users")
    affected_services: List[str] = Field(default_factory=list, description="Affected services")
    revenue_impact: Optional[float] = Field(None, description="Revenue impact in USD")
    
    # Related items
    ticket_ids: List[str] = Field(default_factory=list, description="Related ticket IDs")
    error_ids: List[str] = Field(default_factory=list, description="Related error IDs")
    causality_node_ids: List[str] = Field(default_factory=list, description="Related causality nodes")
    
    # Analysis
    root_cause: Optional[str] = Field(None, description="Root cause analysis")
    contributing_factors: List[str] = Field(default_factory=list, description="Contributing factors")
    resolution_steps: List[str] = Field(default_factory=list, description="Resolution steps taken")
    
    # Prevention
    lessons_learned: Optional[str] = Field(None, description="Lessons learned")
    prevention_measures: List[str] = Field(default_factory=list, description="Prevention measures")
    follow_up_actions: List[str] = Field(default_factory=list, description="Follow-up actions")
    
    # Custom tags and metadata
    tags: Dict[str, str] = Field(default_factory=dict, description="Custom tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }