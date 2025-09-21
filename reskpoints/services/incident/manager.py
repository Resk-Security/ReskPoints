"""Incident management service with automated ticket generation and workflow."""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import uuid

from reskpoints.models.incident import Ticket, CausalityNode, CausalityEdge, IncidentReport
from reskpoints.models.enums import TicketStatus, TicketPriority, TicketSeverity
from reskpoints.core.logging import get_logger

logger = get_logger(__name__)


class EscalationLevel(Enum):
    """Escalation levels for incidents."""
    NONE = "none"
    LEVEL_1 = "level_1"
    LEVEL_2 = "level_2"
    LEVEL_3 = "level_3"
    CRITICAL = "critical"


class IncidentManager:
    """Automated incident management with ticket generation and workflow."""
    
    def __init__(self):
        self.tickets: Dict[str, Ticket] = {}
        self.ticket_workflows: Dict[str, Dict[str, Any]] = {}
        self.escalation_rules = self._setup_escalation_rules()
        self.auto_assignment_rules = self._setup_assignment_rules()
        
        logger.info("Incident manager initialized")
    
    def _setup_escalation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Set up automatic escalation rules."""
        return {
            "critical_no_response": {
                "condition": lambda ticket: (
                    ticket.severity == TicketSeverity.CRITICAL and
                    ticket.status == TicketStatus.OPEN and
                    (datetime.utcnow() - ticket.created_at).total_seconds() > 900  # 15 minutes
                ),
                "action": "escalate_to_level_2",
                "sla_minutes": 15,
            },
            "high_overdue": {
                "condition": lambda ticket: (
                    ticket.priority == TicketPriority.HIGH and
                    ticket.status == TicketStatus.OPEN and
                    (datetime.utcnow() - ticket.created_at).total_seconds() > 3600  # 1 hour
                ),
                "action": "escalate_to_level_1",
                "sla_minutes": 60,
            },
            "medium_overdue": {
                "condition": lambda ticket: (
                    ticket.priority == TicketPriority.MEDIUM and
                    ticket.status == TicketStatus.OPEN and
                    (datetime.utcnow() - ticket.created_at).total_seconds() > 14400  # 4 hours
                ),
                "action": "escalate_to_level_1",
                "sla_minutes": 240,
            },
        }
    
    def _setup_assignment_rules(self) -> List[Dict[str, Any]]:
        """Set up automatic assignment rules."""
        return [
            {
                "condition": lambda ticket: ticket.category == "performance" and "latency" in ticket.title.lower(),
                "assignee": "performance_team",
                "team": "Infrastructure",
            },
            {
                "condition": lambda ticket: ticket.category == "cost" or "budget" in ticket.title.lower(),
                "assignee": "cost_optimization_team",
                "team": "FinOps",
            },
            {
                "condition": lambda ticket: ticket.severity == TicketSeverity.CRITICAL,
                "assignee": "on_call_engineer",
                "team": "SRE",
            },
            {
                "condition": lambda ticket: "anomaly" in ticket.title.lower(),
                "assignee": "data_science_team",
                "team": "DataScience",
            },
        ]
    
    async def create_ticket_from_error(
        self,
        error_data: Dict[str, Any],
        auto_assign: bool = True
    ) -> Ticket:
        """Create ticket automatically from error data."""
        
        # Determine severity and priority based on error
        severity = self._map_error_to_severity(error_data)
        priority = self._map_error_to_priority(error_data)
        category = self._determine_category(error_data)
        
        # Generate title and description
        title = self._generate_title(error_data)
        description = self._generate_description(error_data)
        
        ticket = Ticket(
            title=title,
            description=description,
            status=TicketStatus.OPEN,
            priority=priority,
            category=category,
            severity=severity,
            provider=error_data.get("provider"),
            model_name=error_data.get("model_name"),
            endpoint=error_data.get("endpoint"),
            user_id=error_data.get("user_id"),
            project_id=error_data.get("project_id"),
            error_ids=[error_data.get("error_id")] if error_data.get("error_id") else [],
            tags={"auto_generated": True, "source": "error_detection"},
            metadata={"original_error": error_data},
        )
        
        # Set SLA deadline
        ticket.sla_deadline = self._calculate_sla_deadline(ticket)
        
        # Auto-assign if enabled
        if auto_assign:
            self._auto_assign_ticket(ticket)
        
        # Store ticket
        self.tickets[ticket.id] = ticket
        
        logger.info(f"Created automatic ticket {ticket.id} for error: {title}")
        return ticket
    
    def _map_error_to_severity(self, error_data: Dict[str, Any]) -> TicketSeverity:
        """Map error severity to ticket severity."""
        error_severity = error_data.get("severity", "medium").lower()
        
        mapping = {
            "critical": TicketSeverity.CRITICAL,
            "high": TicketSeverity.HIGH,
            "medium": TicketSeverity.MEDIUM,
            "low": TicketSeverity.LOW,
        }
        
        return mapping.get(error_severity, TicketSeverity.MEDIUM)
    
    def _map_error_to_priority(self, error_data: Dict[str, Any]) -> TicketPriority:
        """Map error data to ticket priority."""
        severity = error_data.get("severity", "medium").lower()
        category = error_data.get("category", "").lower()
        
        # High priority conditions
        if severity == "critical" or category in ["rate_limit", "authentication", "service_unavailable"]:
            return TicketPriority.HIGH
        elif severity == "high" or category in ["timeout", "validation", "quota_exceeded"]:
            return TicketPriority.MEDIUM
        else:
            return TicketPriority.LOW
    
    def _determine_category(self, error_data: Dict[str, Any]) -> str:
        """Determine ticket category from error data."""
        error_category = error_data.get("category", "").lower()
        
        # Map error categories to ticket categories
        category_mapping = {
            "rate_limit": "performance",
            "timeout": "performance",
            "latency": "performance",
            "quota_exceeded": "cost",
            "authentication": "security",
            "authorization": "security",
            "validation": "data_quality",
            "service_unavailable": "infrastructure",
        }
        
        return category_mapping.get(error_category, "general")
    
    def _generate_title(self, error_data: Dict[str, Any]) -> str:
        """Generate descriptive title for ticket."""
        provider = error_data.get("provider", "Unknown")
        model = error_data.get("model_name", "Unknown")
        category = error_data.get("category", "error")
        
        return f"{provider}/{model}: {category.replace('_', ' ').title()} Error"
    
    def _generate_description(self, error_data: Dict[str, Any]) -> str:
        """Generate detailed description for ticket."""
        lines = ["Automatically generated ticket from error detection:"]
        lines.append("")
        
        if error_data.get("message"):
            lines.append(f"Error Message: {error_data['message']}")
        
        if error_data.get("code"):
            lines.append(f"Error Code: {error_data['code']}")
        
        if error_data.get("provider"):
            lines.append(f"Provider: {error_data['provider']}")
        
        if error_data.get("model_name"):
            lines.append(f"Model: {error_data['model_name']}")
        
        if error_data.get("endpoint"):
            lines.append(f"Endpoint: {error_data['endpoint']}")
        
        if error_data.get("timestamp"):
            lines.append(f"Timestamp: {error_data['timestamp']}")
        
        lines.append("")
        lines.append("This ticket was automatically created and assigned based on error detection rules.")
        
        return "\n".join(lines)
    
    def _calculate_sla_deadline(self, ticket: Ticket) -> datetime:
        """Calculate SLA deadline based on ticket properties."""
        base_time = datetime.utcnow()
        
        # SLA times based on severity and priority
        if ticket.severity == TicketSeverity.CRITICAL:
            sla_hours = 2  # 2 hours for critical
        elif ticket.priority == TicketPriority.HIGH:
            sla_hours = 8  # 8 hours for high priority
        elif ticket.priority == TicketPriority.MEDIUM:
            sla_hours = 24  # 24 hours for medium priority
        else:
            sla_hours = 72  # 72 hours for low priority
        
        return base_time + timedelta(hours=sla_hours)
    
    def _auto_assign_ticket(self, ticket: Ticket):
        """Automatically assign ticket based on rules."""
        for rule in self.auto_assignment_rules:
            if rule["condition"](ticket):
                ticket.assignee_id = rule["assignee"]
                ticket.team = rule["team"]
                logger.info(f"Auto-assigned ticket {ticket.id} to {rule['assignee']} ({rule['team']})")
                break
    
    async def update_ticket_status(
        self,
        ticket_id: str,
        new_status: TicketStatus,
        user_id: str,
        notes: Optional[str] = None
    ) -> Optional[Ticket]:
        """Update ticket status with workflow validation."""
        ticket = self.tickets.get(ticket_id)
        if not ticket:
            return None
        
        # Validate status transition
        if not self._is_valid_status_transition(ticket.status, new_status):
            raise ValueError(f"Invalid status transition from {ticket.status} to {new_status}")
        
        old_status = ticket.status
        ticket.status = new_status
        ticket.updated_at = datetime.utcnow()
        
        # Handle status-specific actions
        if new_status == TicketStatus.IN_PROGRESS and not ticket.assignee_id:
            ticket.assignee_id = user_id  # Auto-assign to user who started work
        
        if new_status == TicketStatus.RESOLVED:
            ticket.resolved_at = datetime.utcnow()
            if notes:
                ticket.resolution_notes = notes
        
        if new_status == TicketStatus.CLOSED:
            ticket.closed_at = datetime.utcnow()
        
        # Record workflow event
        await self._record_workflow_event(ticket, old_status, new_status, user_id, notes)
        
        logger.info(f"Updated ticket {ticket_id} status: {old_status} -> {new_status}")
        return ticket
    
    def _is_valid_status_transition(self, current: TicketStatus, new: TicketStatus) -> bool:
        """Validate if status transition is allowed."""
        valid_transitions = {
            TicketStatus.OPEN: [TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED, TicketStatus.CLOSED],
            TicketStatus.IN_PROGRESS: [TicketStatus.OPEN, TicketStatus.RESOLVED, TicketStatus.CLOSED],
            TicketStatus.RESOLVED: [TicketStatus.OPEN, TicketStatus.CLOSED],
            TicketStatus.CLOSED: [TicketStatus.OPEN],  # Allow reopening
        }
        
        return new in valid_transitions.get(current, [])
    
    async def _record_workflow_event(
        self,
        ticket: Ticket,
        old_status: TicketStatus,
        new_status: TicketStatus,
        user_id: str,
        notes: Optional[str]
    ):
        """Record workflow event for audit trail."""
        if ticket.id not in self.ticket_workflows:
            self.ticket_workflows[ticket.id] = {"events": []}
        
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": "status_change",
            "old_status": old_status.value,
            "new_status": new_status.value,
            "notes": notes,
        }
        
        self.ticket_workflows[ticket.id]["events"].append(event)
    
    async def check_escalations(self):
        """Check for tickets that need escalation."""
        escalated_tickets = []
        
        for ticket in self.tickets.values():
            if ticket.status in [TicketStatus.CLOSED]:
                continue
            
            for rule_name, rule in self.escalation_rules.items():
                if rule["condition"](ticket) and not ticket.escalated:
                    await self._escalate_ticket(ticket, rule_name, rule)
                    escalated_tickets.append(ticket.id)
        
        if escalated_tickets:
            logger.warning(f"Escalated {len(escalated_tickets)} tickets: {escalated_tickets}")
        
        return escalated_tickets
    
    async def _escalate_ticket(self, ticket: Ticket, rule_name: str, rule: Dict[str, Any]):
        """Escalate a ticket."""
        ticket.escalated = True
        ticket.escalated_at = datetime.utcnow()
        ticket.updated_at = datetime.utcnow()
        
        # Update priority if needed
        if ticket.priority != TicketPriority.HIGH:
            old_priority = ticket.priority
            ticket.priority = TicketPriority.HIGH
            logger.warning(f"Escalated ticket {ticket.id} priority: {old_priority} -> {ticket.priority}")
        
        # Record escalation event
        await self._record_workflow_event(
            ticket,
            ticket.status,
            ticket.status,
            "system",
            f"Auto-escalated due to rule: {rule_name}"
        )
        
        logger.critical(f"ESCALATED TICKET {ticket.id}: {ticket.title} (Rule: {rule_name})")
    
    def get_ticket_metrics(self) -> Dict[str, Any]:
        """Get ticket metrics and statistics."""
        total_tickets = len(self.tickets)
        if total_tickets == 0:
            return {"total_tickets": 0}
        
        # Status breakdown
        status_counts = {}
        for status in TicketStatus:
            status_counts[status.value] = sum(1 for t in self.tickets.values() if t.status == status)
        
        # Severity breakdown
        severity_counts = {}
        for severity in TicketSeverity:
            severity_counts[severity.value] = sum(1 for t in self.tickets.values() if t.severity == severity)
        
        # Calculate resolution times
        resolved_tickets = [t for t in self.tickets.values() if t.resolved_at]
        avg_resolution_time = None
        if resolved_tickets:
            total_resolution_time = sum(
                (t.resolved_at - t.created_at).total_seconds()
                for t in resolved_tickets
            )
            avg_resolution_time = total_resolution_time / len(resolved_tickets) / 3600  # in hours
        
        # SLA compliance
        overdue_tickets = sum(
            1 for t in self.tickets.values()
            if t.sla_deadline and datetime.utcnow() > t.sla_deadline and t.status != TicketStatus.CLOSED
        )
        
        return {
            "total_tickets": total_tickets,
            "status_breakdown": status_counts,
            "severity_breakdown": severity_counts,
            "average_resolution_time_hours": avg_resolution_time,
            "overdue_tickets": overdue_tickets,
            "escalated_tickets": sum(1 for t in self.tickets.values() if t.escalated),
        }


# Global incident manager instance
incident_manager = IncidentManager()


def get_incident_manager() -> IncidentManager:
    """Get the global incident manager instance."""
    return incident_manager


# Background escalation checking
async def start_incident_monitoring():
    """Start background incident monitoring tasks."""
    async def escalation_check_loop():
        while True:
            try:
                await incident_manager.check_escalations()
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Error in escalation check: {e}")
                await asyncio.sleep(300)
    
    # Start escalation checking task
    asyncio.create_task(escalation_check_loop())
    logger.info("Incident monitoring tasks started")