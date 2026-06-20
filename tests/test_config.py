from reskpoints.config import AgentLoggerConfig


class TestAgentLoggerConfig:
    def test_default_config(self):
        config = AgentLoggerConfig()
        assert config.environment == "development"
        assert config.default_rate == 1.0
        assert config.masking_enabled is True

    def test_custom_config(self):
        config = AgentLoggerConfig({
            "agent_logger": {
                "environment": "production",
                "sampling": {
                    "default_rate": 0.5,
                    "rules": [
                        {"action": "heartbeat", "rate": 0.01},
                        {"action": "tool_*", "rate": 1.0},
                    ],
                },
            }
        })
        assert config.environment == "production"
        assert config.default_rate == 0.5
        assert config.get_sampling_rate("heartbeat") == 0.01
        assert config.get_sampling_rate("tool_call") == 1.0
        assert config.get_sampling_rate("unknown") == 0.5

    def test_env_var_substitution(self, monkeypatch):
        monkeypatch.setenv("ENV", "staging")
        config = AgentLoggerConfig({
            "agent_logger": {
                "environment": "${ENV:development}",
            }
        })
        assert config.environment == "staging"

    def test_env_var_default(self):
        config = AgentLoggerConfig({
            "agent_logger": {
                "environment": "${UNSET_VAR:production}",
            }
        })
        assert config.environment == "production"

    def test_get_platform_config(self):
        config = AgentLoggerConfig({
            "agent_logger": {
                "platforms": {
                    "webhook": {
                        "enabled": True,
                        "url": "http://example.com/hook",
                        "timeout": 5.0,
                    },
                },
            }
        })
        cfg = config.get_platform_config("webhook")
        assert cfg["url"] == "http://example.com/hook"
        assert cfg["timeout"] == 5.0

        default_cfg = config.get_platform_config("nonexistent")
        assert default_cfg == {}
