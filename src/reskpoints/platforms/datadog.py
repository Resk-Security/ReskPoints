from typing import Any

from ..models import ActionLog, LogResult
from .base import BasePlatform


class DatadogPlatform(BasePlatform):
    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.api_key = self.config.get("api_key", "")
        self.site = self.config.get("site", "datadoghq.com")
        self.tags = self.config.get("tags", {})
        self._client = None
        self._setup_client()

    def _setup_client(self):
        if not self.api_key:
            return
        try:
            import datadog_api_client.v2.api.logs_api as logs_api
            from datadog_api_client import ApiClient, Configuration
            self._cfg = Configuration()
            self._cfg.api_key["apiKeyAuth"] = self.api_key
            self._cfg.server_variables["site"] = self.site
            self._client = ApiClient(self._cfg)
            self._logs_api = logs_api.LogsApi(self._client)
        except ImportError:
            self._client = None

    def _emit(self, entry: ActionLog) -> LogResult:
        if self._client is None:
            return LogResult(success=False, platform=self.name, action_id=entry.id, error="datadog_client_not_available")
        try:
            from datadog_api_client.v2.model.content_encoding import ContentEncoding
            from datadog_api_client.v2.model.http_log import HTTPLog
            from datadog_api_client.v2.model.http_log_item import HTTPLogItem
            data = entry.to_dict()
            data["ddsource"] = "reskpoints"
            data["ddtags"] = ",".join(f"{k}:{v}" for k, v in self.tags.items())
            item = HTTPLogItem(
                ddsource="reskpoints",
                ddtags=data["ddtags"],
                message=data,
            )
            self._logs_api.submit_log(content_encoding=ContentEncoding.DEFLATE, body=HTTPLog([item]))
            return LogResult(success=True, platform=self.name, action_id=entry.id)
        except Exception as e:
            return LogResult(success=False, platform=self.name, action_id=entry.id, error=str(e))

    def __del__(self):
        if self._client is not None:
            self._client.close()
