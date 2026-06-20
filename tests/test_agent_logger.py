import pytest

from reskpoints.agent_logger import AgentLogger
from reskpoints.config import AgentLoggerConfig
from reskpoints.models import ActionLog


class TestAgentLogger:
    @pytest.fixture
    def logger(self):
        config = AgentLoggerConfig({
            "agent_logger": {
                "environment": "test",
                "masking": {"enabled": False},
                "sampling": {"default_rate": 1.0},
                "platforms": {
                    "mock": {"enabled": True},
                    "console": {"enabled": False},
                    "file": {"enabled": False},
                    "webhook": {"enabled": False},
                },
            }
        })
        return AgentLogger(config)

    def test_log_basic(self, logger):
        results = logger.log(
            agent_id="agent-1",
            action="tool_call",
            probability=0.95,
            params={"tool": "search", "query": "test"},
            result="success",
        )
        assert len(results) == 1
        assert results[0].success is True

    def test_log_action_method(self, logger):
        entry = ActionLog(agent_id="agent-2", action="send_message", probability=0.8)
        results = logger.log_action(entry)
        assert len(results) == 1
        assert results[0].success is True

    @pytest.mark.asyncio
    async def test_alog_basic(self, logger):
        results = await logger.alog(
            agent_id="agent-1",
            action="async_action",
            probability=0.9,
            params={"key": "value"},
            result="done",
        )
        assert len(results) == 1
        assert results[0].success is True

    def test_sampling_skip(self, logger):
        logger.config.sampling_config["default_rate"] = 0.0
        entry = ActionLog(agent_id="agent-3", action="rare_action")
        results = logger.log_action(entry)
        assert len(results) == 1
        assert results[0].platform == "sampling_skip"

    def test_masking_enabled(self, logger):
        logger.config.masking_config["enabled"] = True
        logger.masker.enabled = True
        logger.masker.sensitive_fields = {"api_key"}
        results = logger.log(
            agent_id="agent-secure",
            action="api_call",
            params={"api_key": "sk-12345", "endpoint": "/v1/chat"},
            sensitive_fields=["api_key"],
        )
        mock_platform = logger.get_platform("mock")
        assert mock_platform is not None
        logged = mock_platform.entries[-1]
        assert "***" in str(logged.parameters.get("api_key", ""))

    def test_health(self, logger):
        health = logger.health()
        assert "mock" in health
        assert health["mock"]["status"] == "ok"

    def test_no_platforms_fallback(self):
        config = AgentLoggerConfig({
            "agent_logger": {
                "platforms": {},
            }
        })
        logger = AgentLogger(config)
        assert "mock" in logger.platforms or len(logger.platforms) > 0
