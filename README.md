# ReskPoints

> Know exactly what your AI agents did, how confident, and what happened.

[![PyPI version](https://img.shields.io/pypi/v/reskpoints.svg)](https://pypi.org/project/reskpoints/)
[![PyPI downloads](https://img.shields.io/pypi/dm/reskpoints.svg)](https://pypi.org/project/reskpoints/)
[![Python Versions](https://img.shields.io/pypi/pyversions/reskpoints.svg)](https://pypi.org/project/reskpoints/)
[![License](https://img.shields.io/pypi/l/reskpoints.svg)](https://github.com/Resk-Security/ReskPoints/blob/main/LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

[![Documentation](https://img.shields.io/badge/docs-resk.fr%2Fdocs%2Fresk-points-orange)](https://resk.fr/docs/resk-points/)

🔗 [resk.fr/projects/reskpoints](https://resk.fr/projects/reskpoints.html) — part of [RESK Security](https://resk.fr)

📚 Guide: [Tool Permissions for AI Agents: Least Privilege in Practice](https://resk.fr/blog/ai-agent-tool-permissions.html)

## Installation

```bash
pip install reskpoints                                    # core (console, file, webhook)
pip install reskpoints[datadog,prometheus,opentelemetry]  # + platforms
```

## Usage rapide (30 seconds)

```python
from reskpoints import AgentLogger

logger = AgentLogger()

logger.log("agent-1", "tool_call", 0.95,
           {"tool": "search", "query": "RAG papers"},
           "3 results")
# → every field enriched: timestamp, host, env, UUID
```

Async? Same API. Decorating a function? One line:

```python
from reskpoints import log_action

@log_action(agent_id="coder")
def execute_python(code: str) -> str: ...

await logger.alog("agent-1", "search", 0.95, {"q": "papers"}, "3 results")
```

## Pourquoi ReskPoints ?

Tracing platforms (Langfuse, Logfire, OpenTelemetry backends) are built for **request tracing** — spans, latencies, token counts. But agent decisions are a different primitive: *which action, with what probability/confidence, which parameters, what result*. ReskPoints models exactly that, with built-in secret masking, per-action sampling, and delivery reliability — and still ships to the observability stack you already run.

| | **ReskPoints** | Langfuse | Logfire / OTel backends | Python `logging` |
|---|---|---|---|---|
| First-class model | Agent action (probability, params, result) | LLM traces | Generic spans | Free-form text |
| One-line decorator | ✅ `@log_action` | ⚠️ SDK callbacks | ⚠️ manual spans | ⚠️ |
| Sensitive-field auto-masking | ✅ built-in | ⚠️ manual | ❌ | ❌ |
| Per-action probabilistic sampling | ✅ (`heartbeat: 1%`, `tool_*: 100%`) | ❌ | ⚠️ global | ❌ |
| Delivery reliability | ✅ retry + circuit breaker + buffering | SaaS-bound | Varies | ❌ |
| Destinations | ✅ 7 (Console, JSONL, Webhook, Datadog, Prometheus, OTel, Mock) — simultaneously | Own SaaS | Own backends | Handlers |
| Replay from file (audit/debug) | ✅ `reskpoints replay` | ❌ | ❌ | ❌ |

## Documentation

- Config reference: `reskpoints.yaml` below
- CLI: `reskpoints log | test | status | tail | replay`

### Quick tour

```python
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

logger.health()
# → {"console": {"status": "ok"}, "datadog": {"status": "degraded", ...}}
```

### CLI

```bash
reskpoints log --agent-id agent-1 --action tool_call --params '{"tool":"search"}'
reskpoints test        # test all platforms
reskpoints status      # platform health
reskpoints tail        # live log stream
reskpoints replay logs.jsonl
```

### Config (`reskpoints.yaml`)

```yaml
agent_logger:
  sampling:
    default_rate: 1.0
    rules:
      - { action: "heartbeat", rate: 0.01 }
      - { action: "tool_*",    rate: 1.0 }
  masking:
    enabled: true
    sensitive_fields: [api_key, token, secret, password]
  platforms:
    console:  { enabled: true, format: "human" }
    webhook:  { enabled: false, url: "${WEBHOOK_URL}", signing_secret: "${WEBHOOK_SECRET}" }
    datadog:  { enabled: false, api_key: "${DD_API_KEY}", site: "datadoghq.eu" }
```

`${ENV_VAR:default}` interpolation is supported throughout.

## Platforms

| Platform | Extra | Use case |
|---|---|---|
| Console | built-in | Dev/debug |
| File (JSONL) | built-in | Local storage, replay |
| Webhook (HMAC-signed) | built-in | Custom endpoints, Zapier, N8n |
| Datadog | `[datadog]` | Logs + Metrics |
| Prometheus | `[prometheus]` | Pushgateway metrics |
| OpenTelemetry | `[opentelemetry]` | OTLP spans → any backend |
| Mock | built-in | Testing |

Every platform is wrapped with exponential-backoff retry, a circuit breaker (5 failures → 30s recovery) and buffering (1000 entries) — one platform going down never kills your logs.

## Development

```bash
git clone https://github.com/Resk-Security/ReskPoints.git
cd ReskPoints
pip install -e ".[all,dev]"
pytest tests/ -v   # 26 tests · ruff clean · mypy passes
```

## Ecosystem

Part of the Resk-Security family: [Resk-LLM](https://github.com/Resk-Security/Resk-LLM) (detection), [resk-logits](https://github.com/Resk-Security/resk-logits) (generation-time defense), [resksecure](https://github.com/Resk-Security/reskSecure) (bitmask firewall).

## License

Apache 2.0 — see [LICENSE](LICENSE).
