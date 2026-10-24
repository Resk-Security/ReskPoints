import hashlib
import hmac
import ipaddress
import socket
from typing import Any, Iterable
from urllib.parse import urlparse

import httpx

from ..models import ActionLog, LogResult
from .base import BasePlatform


def _validate_webhook_url(
    url: str,
    allow_private: bool = False,
    allowed_hosts: Iterable[str] | None = None,
) -> None:
    """Reject non-HTTP(S) URLs and hosts resolving to non-public addresses."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"unsupported scheme {parsed.scheme!r}")
    host = parsed.hostname
    if not host:
        raise ValueError("missing hostname")
    if allowed_hosts is not None and host not in set(allowed_hosts):
        raise ValueError(f"host {host!r} not in allowlist")
    if allow_private:
        return
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise ValueError(f"cannot resolve {host}: {exc}") from exc
    for info in infos:
        ip = ipaddress.ip_address(str(info[4][0]).split("%", 1)[0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            raise ValueError(f"non-public address {ip}")


class WebhookPlatform(BasePlatform):
    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.url = self.config.get("url", "")
        self.headers = self.config.get("headers", {})
        self.signing_secret = self.config.get("signing_secret", "")
        self.timeout = self.config.get("timeout", 10.0)
        self._validation_error = ""
        if self.url:
            try:
                _validate_webhook_url(
                    self.url,
                    allow_private=bool(self.config.get("allow_private", False)),
                    allowed_hosts=self.config.get("allowed_hosts"),
                )
            except ValueError as exc:
                self._validation_error = str(exc)
        self._client = httpx.Client(timeout=self.timeout)
        self._async_client = httpx.AsyncClient(timeout=self.timeout)

    def _emit(self, entry: ActionLog) -> LogResult:
        if not self.url:
            return LogResult(success=False, platform=self.name, action_id=entry.id, error="webhook_url_missing")
        if self._validation_error:
            return LogResult(
                success=False,
                platform=self.name,
                action_id=entry.id,
                error=f"webhook_url_rejected: {self._validation_error}",
            )
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
        if not self.url:
            return LogResult(success=False, platform=self.name, action_id=entry.id, error="webhook_url_missing")
        if self._validation_error:
            return LogResult(
                success=False,
                platform=self.name,
                action_id=entry.id,
                error=f"webhook_url_rejected: {self._validation_error}",
            )
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
