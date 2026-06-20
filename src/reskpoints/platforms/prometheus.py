from typing import Any

from ..models import ActionLog, LogResult
from .base import BasePlatform


class PrometheusPlatform(BasePlatform):
    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.pushgateway_url = self.config.get("pushgateway_url", "http://localhost:9091")
        self.job_name = self.config.get("job_name", "agent_actions")
        self._registry = None
        self._gauge = None
        self._setup_metrics()

    def _setup_metrics(self):
        try:
            from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
            self._registry = CollectorRegistry()
            self._gauge = Gauge(
                "agent_action_total",
                "Total agent actions",
                labelnames=["agent_id", "action", "success"],
                registry=self._registry,
            )
            self._push = push_to_gateway
        except ImportError:
            self._gauge = None

    def _emit(self, entry: ActionLog) -> LogResult:
        labels = [entry.agent_id, entry.action, str(entry.success).lower()]
        if self._gauge is not None and self._registry is not None:
            self._gauge.labels(*labels).inc()
            self._push(
                self.pushgateway_url,
                job=self.job_name,
                registry=self._registry,
            )
        return LogResult(success=True, platform=self.name, action_id=entry.id)
