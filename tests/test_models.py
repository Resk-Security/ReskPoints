from reskpoints.models import ActionLog, LogResult


class TestActionLog:
    def test_default_fields(self):
        entry = ActionLog(agent_id="test-agent", action="test")
        assert entry.agent_id == "test-agent"
        assert entry.action == "test"
        assert entry.probability == 1.0
        assert entry.success is True
        assert entry.parameters == {}
        assert entry.metadata == {}

    def test_to_dict(self):
        entry = ActionLog(
            agent_id="agent-1",
            action="tool_call",
            probability=0.85,
            parameters={"tool": "search"},
            result="found",
        )
        d = entry.to_dict()
        assert d["agent_id"] == "agent-1"
        assert d["action"] == "tool_call"
        assert d["probability"] == 0.85
        assert d["parameters"] == {"tool": "search"}
        assert d["result"] == "found"
        assert "timestamp" in d
        assert "id" in d

    def test_to_dict_roundtrip(self):
        entry = ActionLog(
            agent_id="agent-1",
            action="test_action",
            probability=0.5,
            parameters={"key": "value"},
            result="ok",
            success=True,
            duration_ms=12.3,
        )
        d = entry.to_dict()
        restored = ActionLog.from_dict(d)
        assert restored.agent_id == entry.agent_id
        assert restored.action == entry.action
        assert restored.probability == entry.probability
        assert restored.parameters == entry.parameters
        assert restored.result == entry.result
        assert restored.success == entry.success
        assert restored.duration_ms == entry.duration_ms


class TestLogResult:
    def test_fields(self):
        r = LogResult(success=True, platform="test", action_id="abc")
        assert r.success is True
        assert r.platform == "test"
        assert r.action_id == "abc"

    def test_to_dict(self):
        r = LogResult(success=False, platform="webhook", action_id="x", error="timeout")
        d = r.to_dict()
        assert d["success"] is False
        assert d["error"] == "timeout"
