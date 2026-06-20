# ReskPoints

> **The AI Agent Logger** — track every action your agents take, with probability, parameters, and results. Ship to any platform.

[![PyPI version](https://img.shields.io/pypi/v/reskpoints.svg)](https://pypi.org/project/reskpoints/)
[![Python Versions](https://img.shields.io/pypi/pyversions/reskpoints.svg)](https://pypi.org/project/reskpoints/)
[![License](https://img.shields.io/pypi/l/reskpoints.svg)](https://github.com/Resk-Security/ReskPoints/blob/main/LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

---

You have **AI agents** making decisions — calling tools, executing code, sending messages, searching databases.  
**ReskPoints** captures every action: *what* the agent did, *how confident* it was, *what parameters* it used, and *what happened*.  

Pipe it to **Datadog, Prometheus, OpenTelemetry, webhooks, JSON files, or your console** — all from a single logger.

---

## One line, full trace

```python
from reskpoints import AgentLogger

logger = AgentLogger()

logger.log("agent-1", "tool_call", 0.95, {"tool": "search", "query": "RAG papers"}, "3 results")
```

Async? Same API:

```python
await logger.alog("agent-1", "tool_call", 0.95, {"tool": "search"}, "3 results")
```

Decorator? Wrap any function:

```python
@log_action(agent_id="coder")
def execute_python(code: str) -> str:
    ...
```

---

## Why ReskPoints?

| Problem | ReskPoints |
|---------|------------|
| **"I don't know what my agent is doing"** | Every tool call, API request, and decision is logged with full context |
| **"It's too slow to add logging"** | One decorator, one line of code. Done. |
| **"My logs go everywhere and nowhere"** | Ship to Console, File, Webhook, Datadog, Prometheus, OpenTelemetry — or all at once |
| **"Sensitive data leaks in params"** | Auto-mask api_key, token, password, and custom fields before they leave your app |
| **"I log too much / too little"** | Probabilistic sampling per action pattern (`heartbeat: 1%`, `tool_*: 100%`) |
| **"One platform going down kills my logs"** | Retry + backoff + circuit breaker + in-memory buffering |

---

## Install

```bash
pip install reskpoints
pip install reskpoints[datadog,prometheus,opentelemetry]  # with extras
```

---

## Features

- **AgentLogger** — sync `log()` and async `alog()` with auto-enrichment (timestamp, host, env, UUID)
- **Decorator** — `@log_action` logs every call automatically with params + result + duration
- **Sampling** — per-action probabilistic rate (`tool_call: 100%`, `heartbeat: 1%`)
- **Masking** — automatic redaction of sensitive fields (`api_key`, `token`, `password`, regex patterns)
- **7 platforms** — Console, File (JSONL), Webhook (HMAC-signed), Datadog, Prometheus, OpenTelemetry, Mock
- **Reliability** — exponential backoff retry, circuit breaker, buffering, batching
- **CLI** — `reskpoints log`, `test`, `status`, `tail`, `replay`
- **Config** — YAML-driven with `${ENV_VAR:default}` interpolation

---

## Platforms

| Platform | Extra | Use case |
|----------|-------|----------|
| Console | *built-in* | Dev/debug |
| File (JSONL) | *built-in* | Local storage, replay |
| Webhook | *built-in* | Custom endpoints, Zapier, N8n |
| Datadog | `[datadog]` | Datadog Logs + Metrics |
| Prometheus | `[prometheus]` | Pushgateway metrics |
| OpenTelemetry | `[opentelemetry]` | OTLP spans → any backend |
| Mock | *built-in* | Testing |

---

## Architecture

```
Agent code                         ReskPoints                     Your observability stack
─────────────────────────────────────────────────────────────────────────────────────

@log_action                          ┌─────────────┐                ┌──────────┐
def search(q):         ───────────▶  │  Sampler    │                │  Console │
  ...                                │  (rate per  │                ├──────────┤
                                     │   action)   │                │  File    │
logger.log(                          └──────┬──────┘                ├──────────┤
  agent_id="agent-1",                       │                       │  Webhook │
  action="tool_call",              ┌────────▼───────┐               ├──────────┤
  probability=0.95,                │   FieldMasker  │               │  Datadog │
  params={...},                    │  (auto-redact  │               ├──────────┤
  result="ok",                     │   secrets)     │               │Prometheus│
)                                  └────────┬───────┘               ├──────────┤
                                           │                       │  OTel    │
                                   ┌───────▼────────┐              └──────────┘
                                   │   MultiPlatform │
                                   │  ┌──────────┐  │
                                   │  │  retry   │  │
                                   │  │  circuit │  │
                                   │  │  buffer  │  │
                                   │  └──────────┘  │
                                   └────────────────┘
```

Each platform is wrapped with retry (exp backoff), circuit breaker (5 fails → 30s recovery), and buffering (1000 entries).

---

## Quick tour

```python
# Minimal
logger.log("agent-1", "search", 0.95, {"q": "papers"}, "3 results")

# Full
logger.log(
    agent_id="agent-1",
    action="tool_call",
    probability=0.95,
    params={"tool": "search", "query": "RAG papers 2025"},
    result=["paper1", "paper2"],
    success=True,
    duration_ms=1240.5,
    session_id="sess_abc123",
    correlation_id="req_xyz789",
)

# Async
results = await logger.alog("agent-1", "search", 0.95, {"q": "papers"}, "3 results")

# Decorator
@log_action(agent_id="coder")
def execute_python(code: str) -> str: ...

# Check health
logger.health()
# → {"console": {"status": "ok"}, "datadog": {"status": "degraded", "error": ...}}
```

---

## CLI

```bash
reskpoints log --agent-id agent-1 --action tool_call --params '{"tool":"search"}'
reskpoints test                    # Test all platforms
reskpoints status                  # Platform health
reskpoints tail                    # Live log stream
reskpoints replay logs.jsonl       # Replay from file
```

---

## Config (`reskpoints.yaml`)

```yaml
agent_logger:
  sampling:
    default_rate: 1.0
    rules:
      - action: "heartbeat"   rate: 0.01
      - action: "tool_*"      rate: 1.0
  masking:
    enabled: true
    sensitive_fields: [api_key, token, secret, password]
  platforms:
    console:
      enabled: true
      format: "human"
    webhook:
      enabled: false
      url: "${WEBHOOK_URL}"
      signing_secret: "${WEBHOOK_SECRET}"
    datadog:
      enabled: false
      api_key: "${DD_API_KEY}"
      site: "datadoghq.eu"
```

---

## Development

```bash
git clone https://github.com/Resk-Security/ReskPoints.git
cd ReskPoints
pip install -e ".[all,dev]"
pytest tests/ -v     # 26 tests
ruff check src/      # clean
mypy src/            # passes
```

---

## License

MIT. Built with [resklogits](https://github.com/Resk-Security/resk-logits).
