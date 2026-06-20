# ReskPoints

**Agent Action Logging Platform** — Log all AI/LLM agent actions to any platform with probability, parameters, and results.

[![PyPI version](https://img.shields.io/pypi/v/reskpoints.svg)](https://pypi.org/project/reskpoints/)
[![Python Versions](https://img.shields.io/pypi/pyversions/reskpoints.svg)](https://pypi.org/project/reskpoints/)
[![License](https://img.shields.io/pypi/l/reskpoints.svg)](https://github.com/Resk-Security/ReskPoints/blob/main/LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

---

## Features

- **AgentLogger** — sync (`log`) and async (`alog`) API
- **Decorator** — `@log_action` auto-logs every function call
- **Probabilistic sampling** — configurable rate per action pattern
- **Field masking** — automatic redaction of sensitive fields (api_key, token, etc.)
- **Multi-platform** — Console, File, Webhook, Prometheus, Datadog, OpenTelemetry, Mock
- **Reliability** — Retry with exponential backoff, circuit breaker, buffering, batching
- **CLI** — `reskpoints log`, `test`, `status`, `tail`, `replay`
- **Config-driven** — YAML configuration with env variable interpolation

---

## Installation

```bash
pip install reskpoints
```

With optional platform support:

```bash
pip install reskpoints[all]          # All platforms
pip install reskpoints[datadog]      # Datadog support
pip install reskpoints[prometheus]   # Prometheus support
pip install reskpoints[opentelemetry]# OpenTelemetry support
```

From source:

```bash
git clone https://github.com/Resk-Security/ReskPoints.git
cd ReskPoints
pip install -e ".[all,dev]"
```

---

## Quick Start

```python
from reskpoints import AgentLogger

logger = AgentLogger()

logger.log(
    agent_id="agent-1",
    action="tool_call",
    probability=0.95,
    params={"tool": "search", "query": "test"},
    result="found 3 results",
)
```

---

## API Reference

### AgentLogger

```python
class AgentLogger(config: AgentLoggerConfig | str | Path | None = None)
```

#### Methods

| Method | Description |
|--------|-------------|
| `log(agent_id, action, probability, params, result, ...)` | Log an action (sync) → `list[LogResult]` |
| `alog(agent_id, action, probability, params, result, ...)` | Log an action (async) → `list[LogResult]` |
| `log_action(entry: ActionLog)` | Log a pre-built ActionLog (sync) |
| `alog_action(entry: ActionLog)` | Log a pre-built ActionLog (async) |
| `flush()` | Force flush all buffered entries |
| `health()` | Return platform health statuses |
| `get_platform(name)` | Get a platform instance by name |

#### Full signature

```python
logger.log(
    agent_id: str,
    action: str,
    probability: float = 1.0,
    params: dict | None = None,
    result: Any = None,
    success: bool = True,
    duration_ms: float | None = None,
    session_id: str | None = None,
    correlation_id: str | None = None,
    sensitive_fields: list[str] | None = None,
    **metadata,
) -> list[LogResult]
```

### Decorator

```python
from reskpoints import log_action

@log_action(agent_id="search-agent")
def search_database(query: str, limit: int = 10) -> list:
    """Automatically logs every call with params and result."""
    return execute_query(query, limit)

# Override action name:
@log_action(agent_id="worker", action_name="custom_action")
def my_func():
    ...
```

### ActionLog

```python
@dataclass
class ActionLog:
    id: str                     # Auto-generated UUID
    agent_id: str
    session_id: str | None
    correlation_id: str | None
    action: str
    probability: float          # 0.0 to 1.0
    parameters: dict
    result: Any
    success: bool
    duration_ms: float | None
    timestamp: datetime
    environment: str
    host: str
    metadata: dict
    sensitive_fields: list[str] # Fields to mask before sending
```

---

## Configuration

Create a `reskpoints.yaml` file:

```yaml
agent_logger:
  environment: "${ENV:development}"

  masking:
    enabled: true
    sensitive_fields:
      - api_key
      - password
      - token
      - secret

  sampling:
    default_rate: 1.0
    rules:
      - action: "heartbeat"
        rate: 0.01
      - action: "tool_*"
        rate: 1.0

  retry:
    max_attempts: 3
    backoff: [0.5, 1.5, 4.5]
    circuit_breaker:
      threshold: 5
      recovery_time: 30

  platforms:
    console:
      enabled: true
      format: "human"   # or "json"
    webhook:
      enabled: false
      url: "${WEBHOOK_URL}"
      signing_secret: "${WEBHOOK_SECRET}"
      timeout: 10.0
    file:
      enabled: false
      path: "/var/log/agent_actions.jsonl"
    datadog:
      enabled: false
      api_key: "${DD_API_KEY}"
      site: "datadoghq.eu"
    prometheus:
      enabled: false
      pushgateway_url: "http://localhost:9091"
```

---

## CLI

```bash
# Log an action
reskpoints log --agent-id agent-1 --action tool_call --params '{"tool":"search"}'

# Test all enabled platforms
reskpoints test

# Show platform health
reskpoints status

# Live tail (console output)
reskpoints tail

# Replay from JSONL file
reskpoints replay /var/log/agent_actions.jsonl
```

All commands accept `--config, -c` to specify a config path.

---

## Platforms

| Platform | Class | Dependencies | Extra |
|----------|-------|-------------|-------|
| Console | `ConsolePlatform` | built-in | Format: human or JSON |
| File | `FilePlatform` | built-in | JSON Lines output |
| Webhook | `WebhookPlatform` | built-in | HMAC signing support |
| Prometheus | `PrometheusPlatform` | `prometheus-client` | Pushgateway |
| Datadog | `DatadogPlatform` | `datadog-api-client` | Logs API |
| OpenTelemetry | `OpenTelemetryPlatform` | `opentelemetry-api` | OTLP traces |
| Mock | `MockPlatform` | built-in | In-memory for tests |

### Using a platform directly

```python
from reskpoints.platforms import WebhookPlatform

platform = WebhookPlatform({
    "url": "https://hooks.example.com/logs",
    "signing_secret": "my-secret",
    "timeout": 5.0,
})
result = platform.emit(action_log)
```

---

## Async Usage

```python
import asyncio
from reskpoints import AgentLogger

async def main():
    logger = AgentLogger()

    # Single action
    results = await logger.alog(
        agent_id="agent-1",
        action="search",
        probability=0.95,
        params={"q": "hello"},
        result="ok",
    )

    # Multiple concurrent actions
    tasks = [
        logger.alog(agent_id=f"agent-{i}", action="task", probability=1.0)
        for i in range(10)
    ]
    all_results = await asyncio.gather(*tasks)

asyncio.run(main())
```

---

## Architecture

```
Agent Action
     │
     ▼
┌─────────────────────────────────────┐
│         AgentLogger                  │
│  ┌────────┐  ┌────────┐  ┌───────┐ │
│  │Sampler │→ │ Masker │→ │Platforms│ │
│  │(prob.  │  │(fields │  │(multi) │ │
│  │ filter)│  │ +regex)│  └───┬───┘ │
│  └────────┘  └────────┘      │     │
└──────────────────────────────┼─────┘
                               │
  ┌────────────┬────────┬──────┼──────┬──────────┐
  ▼            ▼        ▼      ▼      ▼          ▼
Console    File     Webhook  DDog  Prometheus  OTel
```

Each platform has built-in:
- **Retry** — exponential backoff (0.5s, 1.5s, 4.5s)
- **Circuit breaker** — opens after 5 failures, recovers in 30s
- **Buffering** — queues up to 1000 entries in memory
- **Async** — native `aemit()` for event loop integration

---

## Development

```bash
# Clone
git clone https://github.com/Resk-Security/ReskPoints.git
cd ReskPoints

# Install with dev deps
pip install -e ".[all,dev]"

# Run tests
pytest tests/ -v

# Lint
ruff check src/

# Type check
mypy src/
```

---

## License

MIT License — see [LICENSE](LICENSE).

Built with [resklogits](https://github.com/Resk-Security/resk-logits) for pattern matching and rule engine capabilities.
