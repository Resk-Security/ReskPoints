# ReskPoints

**Agent Action Logging Platform** — Log all AI/LLM agent actions to any platform with probability, parameters, and results.

## Quick Start

```bash
uv pip install reskpoints
```

## Usage

### Basic

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

### Async

```python
import asyncio
from reskpoints import AgentLogger

async def main():
    logger = AgentLogger()
    results = await logger.alog(
        agent_id="agent-1",
        action="async_action",
        probability=0.9,
        params={"key": "value"},
        result="done",
    )

asyncio.run(main())
```

### Decorator

```python
from reskpoints import log_action

@log_action(agent_id="my-agent")
def search(query: str) -> str:
    return f"Results for {query}"
```

### Custom config

```python
from reskpoints import AgentLogger

logger = AgentLogger("config.yaml")
```

## CLI

```bash
# Log an action
reskpoints log --agent-id agent-1 --action tool_call --params '{"tool":"search"}'

# Test all platforms
reskpoints test

# Check platform health
reskpoints status

# Live tail logs
reskpoints tail

# Replay logs from JSONL file
reskpoints replay /var/log/agent_actions.jsonl
```

## Platforms

| Platform | Class | Dependencies |
|----------|-------|-------------|
| Console | `ConsolePlatform` | built-in |
| File (JSONL) | `FilePlatform` | built-in |
| Webhook | `WebhookPlatform` | built-in |
| Prometheus | `PrometheusPlatform` | `prometheus-client` |
| Datadog | `DatadogPlatform` | `datadog-api-client` |
| OpenTelemetry | `OpenTelemetryPlatform` | `opentelemetry-api` |
| Mock | `MockPlatform` | built-in (testing) |

## Architecture

```
Agent Action
     │
     ▼
┌─────────────────────────────────────────────┐
│            AgentLogger                       │
│  ┌──────┐  ┌──────────┐  ┌───────────────┐ │
│  │Sampler│→│  Masker   │→│  Platforms     │ │
│  └──────┘  └──────────┘  │  ┌───────────┐ │ │
│                           │  │ Webhook   │ │ │
│                           │  ├───────────┤ │ │
│                           │  │ Datadog   │ │ │
│                           │  ├───────────┤ │ │
│                           │  │ Prometheus│ │ │
│                           │  ├───────────┤ │ │
│                           │  │ Console   │ │ │
│                           │  ├───────────┤ │ │
│                           │  │ File      │ │ │
│                           │  └───────────┘ │ │
│                           └─────────────────┘ │
└─────────────────────────────────────────────┘
     │
     ▼
  LogResult[]
```

## Built with

- **Python 3.10+**
- **httpx** — async HTTP
- **Pydantic** — data validation
- **resklogits** — pattern matching, rule engine, YAML config parsing
