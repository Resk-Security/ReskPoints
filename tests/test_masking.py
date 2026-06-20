from reskpoints.masking import FieldMasker


class TestFieldMasker:
    def test_mask_sensitive_field(self):
        masker = FieldMasker(sensitive_fields=["api_key"])
        result = masker.mask({"api_key": "sk-1234567890abcdef", "name": "test"})
        assert result["name"] == "test"
        assert result["api_key"] != "sk-1234567890abcdef"
        assert "****" in result["api_key"]

    def test_mask_nested(self):
        masker = FieldMasker(sensitive_fields=["token"])
        result = masker.mask({"data": {"token": "secret123", "user": "alice"}})
        assert result["data"]["user"] == "alice"
        assert "****" in result["data"]["token"]

    def test_mask_disabled(self):
        masker = FieldMasker(sensitive_fields=["key"], enabled=False)
        result = masker.mask({"key": "visible"})
        assert result["key"] == "visible"

    def test_regex_masking(self):
        masker = FieldMasker(
            sensitive_fields=[],
            patterns=[(r"\b[A-Za-z0-9_]{20,}\b", "***")],
        )
        result = masker.mask({"text": "my token is abcdefghijklmnopqrst"})
        assert "**" in result["text"]
