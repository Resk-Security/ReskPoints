import json
import tempfile
from pathlib import Path

from reskpoints.models import ActionLog
from reskpoints.platforms import ConsolePlatform, FilePlatform, MockPlatform, WebhookPlatform


class TestMockPlatform:
    def test_emit(self):
        p = MockPlatform({"enabled": True})
        entry = ActionLog(agent_id="test", action="test_action")
        result = p.emit(entry)
        assert result.success is True
        assert len(p.entries) == 1
        assert p.entries[0].action == "test_action"

    def test_emit_failure(self):
        p = MockPlatform({"enabled": True})
        p.set_fail(True)
        entry = ActionLog(agent_id="test", action="fail")
        result = p.emit(entry)
        assert result.success is False
        assert "mock" in (result.error or "").lower()


class TestFilePlatform:
    def test_emit(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            path = f.name

        try:
            p = FilePlatform({"enabled": True, "path": path})
            entry = ActionLog(agent_id="test", action="file_test", result="logged")
            result = p.emit(entry)
            assert result.success is True

            with open(path, encoding="utf-8") as f:
                line = f.readline().strip()
                data = json.loads(line)
                assert data["agent_id"] == "test"
                assert data["action"] == "file_test"
        finally:
            Path(path).unlink(missing_ok=True)


class TestConsolePlatform:
    def test_emit(self, capsys):
        p = ConsolePlatform({"enabled": True, "format": "json"})
        entry = ActionLog(agent_id="test", action="console_test", probability=0.9)
        result = p.emit(entry)
        assert result.success is True
        captured = capsys.readouterr()
        assert "test" in captured.out


class TestWebhookPlatform:
    def test_emit_fails_without_url(self):
        p = WebhookPlatform({"enabled": True, "url": ""})
        entry = ActionLog(agent_id="test", action="webhook_test")
        result = p.emit(entry)
        assert result.success is False


class TestWebhookSSRF:
    def test_rejects_private_and_non_http_urls(self):
        for url in (
            "http://127.0.0.1:8000/hook",
            "http://169.254.169.254/latest/meta-data",
            "file:///etc/passwd",
        ):
            p = WebhookPlatform({"enabled": True, "url": url})
            result = p.emit(ActionLog(agent_id="test", action="ssrf"))
            assert result.success is False
            assert "rejected" in (result.error or "")

    def test_allows_private_when_explicitly_enabled(self):
        p = WebhookPlatform({"enabled": True, "url": "http://127.0.0.1:9/hook", "allow_private": True})
        assert p._validation_error == ""
