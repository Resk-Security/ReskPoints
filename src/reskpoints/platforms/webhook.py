import hmac
import hashlib
from typing import Any

import httpx

from ..models import ActionLog, LogResult
from .base import BasePlatform


class WebhookPlatform(BasePlatform):
    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.url = self.config.get("url", "")
        self.headers = self.config.get("headers", {})
        self.signing_secret = self.config.get("signing_secret", "")
        self.timeout = self.config.get("timeout", 10.0)
        self._client = httpx.Client(timeout=self.timeout)
        self._async_client = httpx.AsyncClient(timeout=self.timeout)

    def _emit(self, entry: ActionLog) -> LogResult:
        payload = entry.to_dict()
        headers = dict(self.headers)
        headers["Content-Type"] = "application/json"

        if self.signing_secret:
            body = __import__("json").dumps(payload, default=str)
            signature = hmac.new(
                self.signing_secret.encode(),
                body.encode(),
                hashlib.sha256,
            ).hexdigest()
            headers["X-Signature-256"] = signature

        response = self._client.post(self.url, json=payload, headers=headers)
        response.raise_for_status()
        return LogResult(success=True, platform=self.name, action_id=entry.id)

    async def _aemit(self, entry: ActionLog) -> LogResult:
        payload = entry.to_dict()
        headers = dict(self.headers)
        headers["Content-Type"] = "application/json"

        if self.signing_secret:
            body = __import__("json").dumps(payload, default=str)
            signature = hmac.new(
                self.signing_secret.encode(),
                body.encode(),
                hashlib.sha256,
            ).hexdigest()
            headers["X-Signature-256"] = signature

        response = await self._async_client.post(self.url, json=payload, headers=headers)
        response.raise_for_status()
        return LogResult(success=True, platform=self.name, action_id=entry.id)
