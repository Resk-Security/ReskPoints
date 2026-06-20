import re
from typing import Any

DEFAULT_SENSITIVE_FIELDS = [
    "api_key",
    "api_key",
    "password",
    "token",
    "secret",
    "authorization",
    "auth_token",
    "access_token",
    "refresh_token",
    "private_key",
    "session_id",
]

DEFAULT_PATTERNS: list[tuple[str, str]] = [
    (r"\b[A-Za-z0-9_\-]{20,}\b", "***"),
    (r"\b(?:sk-[a-zA-Z0-9]{20,}|pk-[a-zA-Z0-9]{20,})\b", "sk-***"),
    (r"\b[A-Za-z0-9+/]{40,}(?:=){0,2}\b", "***"),
]


class FieldMasker:
    def __init__(
        self,
        sensitive_fields: list[str] | None = None,
        patterns: list[tuple[str, str]] | None = None,
        enabled: bool = True,
    ):
        self.sensitive_fields = set(sensitive_fields or DEFAULT_SENSITIVE_FIELDS)
        self.patterns = [(re.compile(p), m) for p, m in (patterns or DEFAULT_PATTERNS)]
        self.enabled = enabled

    def mask(self, data: dict[str, Any], extra_fields: list[str] | None = None) -> dict[str, Any]:
        if not self.enabled:
            return data

        fields_to_mask = self.sensitive_fields | set(extra_fields or [])
        result: dict[str, Any] = {}

        for key, value in data.items():
            if key in fields_to_mask:
                result[key] = self._mask_value(value)
            elif isinstance(value, dict):
                result[key] = self._mask_nested(value, fields_to_mask, depth=0)
            elif isinstance(value, str):
                result[key] = self._apply_regex(value)
            else:
                result[key] = value

        return result

    def _mask_value(self, value: Any) -> str:
        s = str(value)
        if len(s) <= 4:
            return "****"
        return s[:2] + "****" + s[-2:] if len(s) > 6 else "****"

    def _mask_nested(
        self, data: dict[str, Any], fields_to_mask: set[str], depth: int = 0
    ) -> dict[str, Any]:
        if depth > 5:
            return {"_masked": "too_deep"}
        result: dict[str, Any] = {}
        for key, value in data.items():
            if key in fields_to_mask:
                result[key] = self._mask_value(value)
            elif isinstance(value, dict):
                result[key] = self._mask_nested(value, fields_to_mask, depth + 1)
            elif isinstance(value, str):
                result[key] = self._apply_regex(value)
            else:
                result[key] = value
        return result

    def _apply_regex(self, value: str) -> str:
        for pattern, replacement in self.patterns:
            if pattern.search(value):
                return pattern.sub(replacement, value)
        return value
