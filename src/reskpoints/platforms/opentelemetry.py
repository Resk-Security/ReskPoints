from typing import Any

from ..models import ActionLog, LogResult
from .base import BasePlatform


class OpenTelemetryPlatform(BasePlatform):
    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.endpoint = self.config.get("endpoint", "http://localhost:4318")
        self.service_name = self.config.get("service_name", "reskpoints")
        self._provider = None
        self._setup_tracing()

    def _setup_tracing(self):
        try:
            from opentelemetry import trace
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            resource = Resource.create({"service.name": self.service_name})
            self._provider = TracerProvider(resource=resource)
            exporter = OTLPSpanExporter(endpoint=f"{self.endpoint}/v1/traces")
            self._provider.add_span_processor(BatchSpanProcessor(exporter))
            self._tracer = self._provider.get_tracer("reskpoints")
        except ImportError:
            self._tracer = None

    def _emit(self, entry: ActionLog) -> LogResult:
        if self._tracer is None:
            return LogResult(
                success=False,
                platform=self.name,
                action_id=entry.id,
                error="opentelemetry_client_not_available",
            )
        with self._tracer.start_as_current_span(entry.action) as span:
            span.set_attribute("agent.id", entry.agent_id)
            span.set_attribute("action", entry.action)
            span.set_attribute("probability", entry.probability)
            span.set_attribute("success", str(entry.success))
            span.set_attribute("duration_ms", entry.duration_ms or 0)
            span.set_attribute("session_id", entry.session_id or "")
            span.set_attribute("correlation_id", entry.correlation_id or "")
            span.set_attribute("environment", entry.environment)
            if entry.parameters:
                for k, v in entry.parameters.items():
                    if isinstance(v, (str, bool, int, float)):
                        span.set_attribute(f"param.{k}", v)
        return LogResult(success=True, platform=self.name, action_id=entry.id)

    def __del__(self):
        if self._provider is not None:
            self._provider.shutdown()
