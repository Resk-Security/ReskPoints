# ReskPoints

> **AI Metrics Monitoring & Cost Tracking System**

ReskPoints is a comprehensive platform for monitoring AI model performance, tracking costs, and managing incidents across multiple AI providers. Built with FastAPI, it provides real-time insights into your AI infrastructure with enterprise-grade monitoring capabilities.

## 🚀 Features

### ✅ **Core Monitoring**
- **Real-time AI Metrics**: Track latency, throughput, error rates, and custom metrics
- **Multi-provider Support**: OpenAI, Anthropic, Google, Azure, and custom endpoints
- **Anomaly Detection**: Statistical and ML-based detection with configurable thresholds
- **Health Monitoring**: Comprehensive health checks and system status

### ✅ **Cost Intelligence**
- **Token Tracking**: Detailed token usage and cost calculation per provider
- **Budget Management**: Set limits, alerts, and optimization recommendations
- **Cost Analytics**: Breakdown by user, project, model, and time period
- **Predictive Insights**: Cost forecasting based on usage patterns

### ✅ **Incident Management**
- **Automated Ticketing**: Auto-generate tickets from errors and anomalies
- **Causality Analysis**: Graph-based error relationship tracking
- **Workflow Management**: Configurable ticket workflows and escalation
- **Impact Analysis**: Understand error propagation and root causes

### ✅ **Enterprise Ready**
- **Scalable Architecture**: Microservices with TimescaleDB, ClickHouse, Redis
- **Security**: JWT authentication, RBAC, audit logging, data encryption
- **Observability**: Prometheus metrics, structured logging, distributed tracing
- **API-First**: Comprehensive REST API with interactive documentation

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │    │   ReskPoints    │    │   Monitoring    │
│                 │    │     Core        │    │    & Alerts     │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • OpenAI APIs   │────┤ • FastAPI App   │────┤ • Prometheus    │
│ • Custom APIs   │    │ • Async Workers │    │ • Grafana       │
│ • Webhooks      │    │ • Business Logic│    │ • Alert Manager │
│ • Direct SDKs   │    │ • Data Pipeline │    │ • Notifications │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                    ┌─────────────────┐
                    │   Data Layer    │
                    ├─────────────────┤
                    │ • PostgreSQL    │
                    │ • TimescaleDB   │
                    │ • ClickHouse    │
                    │ • Redis Cache   │
                    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose (recommended)
- PostgreSQL, Redis (for production)

### Option 1: Docker Development (Recommended)
```bash
# Clone the repository
git clone https://github.com/Resk-Security/ReskPoints.git
cd ReskPoints

# Start full development stack
cd deployments/docker
docker-compose up

# Access services:
# • API: http://localhost:8000
# • API Docs: http://localhost:8000/docs
# • Prometheus: http://localhost:9090
# • Grafana: http://localhost:3000 (admin/admin)
```

### Option 2: Local Development
```bash
# Clone and setup
git clone https://github.com/Resk-Security/ReskPoints.git
cd ReskPoints

# Setup development environment
./scripts/setup-dev.sh

# Activate virtual environment
source venv/bin/activate

# Start development server
uvicorn reskpoints.main:create_app --reload --host 0.0.0.0 --port 8000
```

### Option 3: Production Deployment
```bash
# Build production image
docker build -f deployments/docker/Dockerfile --target production -t reskpoints:latest .

# Run with environment variables
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:pass@host:5432/reskpoints" \
  -e REDIS_URL="redis://host:6379/0" \
  -e SECRET_KEY="your-secret-key-here" \
  reskpoints:latest
```

## 📊 API Usage Examples

### Submit AI Metrics
```bash
curl -X POST http://localhost:8000/api/v1/metrics/submit \
  -H "Content-Type: application/json" \
  -d '{
    "metric_type": "latency",
    "value": 150.5,
    "unit": "ms",
    "provider": "openai",
    "model_name": "gpt-3.5-turbo",
    "endpoint": "/v1/chat/completions",
    "user_id": "user_123",
    "project_id": "project_456",
    "metadata": {
      "region": "us-east-1",
      "environment": "production"
    }
  }'
```

### Track Costs & Token Usage
```bash
curl -X POST http://localhost:8000/api/v1/cost/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "model_name": "gpt-3.5-turbo",
    "endpoint": "/v1/chat/completions",
    "user_id": "user_123",
    "project_id": "project_456",
    "success": true,
    "token_usage": {
      "input_tokens": 100,
      "output_tokens": 50,
      "total_tokens": 150
    },
    "cost_breakdown": {
      "input_cost": 0.001,
      "output_cost": 0.002,
      "total_cost": 0.003
    }
  }'
```

### Create Incident Tickets
```bash
curl -X POST http://localhost:8000/api/v1/incidents/tickets \
  -H "Content-Type: application/json" \
  -d '{
    "title": "High latency detected in OpenAI GPT-3.5",
    "description": "Average response time exceeded 2s threshold",
    "priority": "high",
    "category": "performance",
    "severity": "high",
    "affected_service": "openai-gpt-3.5",
    "metadata": {
      "metric_threshold": "2000ms",
      "current_value": "2850ms",
      "detection_time": "2024-01-15T10:30:00Z"
    }
  }'
```

### Query Cost Analytics
```bash
# Get cost summary for a project
curl "http://localhost:8000/api/v1/cost/summary?project_id=project_456&days=30"

# Get budget alerts
curl "http://localhost:8000/api/v1/cost/budget-alerts?project_id=project_456"

# Get cost breakdown by model
curl "http://localhost:8000/api/v1/cost/breakdown?group_by=model_name&days=7"
```

## 🔧 Configuration

Create a `.env` file in the project root:

```env
# Application Settings
DEBUG=true
HOST=0.0.0.0
PORT=8000
SECRET_KEY=your-secret-key-change-in-production

# Database URLs
DATABASE_URL=postgresql://user:pass@localhost:5432/reskpoints
TIMESCALE_URL=postgresql://user:pass@localhost:5433/reskpoints_metrics
CLICKHOUSE_URL=http://localhost:8123
REDIS_URL=redis://localhost:6379/0

# External Integrations
ALERT_WEBHOOK_URL=https://hooks.slack.com/services/your/webhook/url

# Security & Auth
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
RATE_LIMIT_REQUESTS=100

# Monitoring
PROMETHEUS_PORT=9090
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Environment-Specific Configuration

<details>
<summary><b>Development</b></summary>

```env
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://postgres:password@localhost:5432/reskpoints_dev
REDIS_URL=redis://localhost:6379/1
```
</details>

<details>
<summary><b>Production</b></summary>

```env
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql://user:secure_pass@prod-db:5432/reskpoints
TIMESCALE_URL=postgresql://user:secure_pass@timescale-prod:5432/metrics
CLICKHOUSE_URL=http://clickhouse-prod:8123
REDIS_URL=redis://redis-prod:6379/0
SECRET_KEY=production-secret-key-256-bit
```
</details>

## 📈 Monitoring & Observability

### Health Checks
- **Liveness**: `GET /live` - Basic application health
- **Readiness**: `GET /ready` - Service dependencies health
- **Detailed Health**: `GET /api/v1/health/` - Comprehensive system status

### Metrics Collection
ReskPoints exposes Prometheus metrics at `/metrics`:

```
# HELP reskpoints_requests_total Total HTTP requests
# TYPE reskpoints_requests_total counter
reskpoints_requests_total{method="POST",endpoint="/api/v1/metrics/submit"} 1250

# HELP reskpoints_request_duration_seconds Request duration
# TYPE reskpoints_request_duration_seconds histogram
reskpoints_request_duration_seconds_bucket{le="0.1"} 1100
```

### Pre-configured Dashboards
When using Docker Compose, Grafana includes:
- **API Performance**: Request rates, latencies, error rates
- **Cost Analytics**: Cost trends, budget tracking, optimization opportunities
- **System Health**: Database connections, cache hit rates, queue sizes
- **Business Metrics**: Token usage, model performance, user activity

## 🛠️ Development

### Project Structure
```
reskpoints/
├── api/                    # FastAPI routes and middleware
│   ├── v1/                # API version 1 endpoints
│   │   ├── metrics.py     # Metrics collection endpoints
│   │   ├── cost.py        # Cost tracking endpoints
│   │   ├── incidents.py   # Incident management endpoints
│   │   └── health.py      # Health check endpoints
│   └── middleware/        # Authentication, CORS, etc.
├── core/                  # Core configuration and utilities
│   ├── config.py         # Application settings
│   ├── logging.py        # Structured logging setup
│   └── security.py       # Security utilities
├── models/               # Pydantic data models
│   ├── metrics.py        # AI metrics models
│   ├── cost.py           # Cost tracking models
│   ├── incident.py       # Incident management models
│   └── enums.py          # Shared enumerations
├── services/             # Business logic layer
│   ├── metrics/          # Metrics collection and analysis
│   ├── cost/             # Cost calculation and optimization
│   ├── incident/         # Incident management workflows
│   ├── causality/        # Causality graph analysis
│   └── monitoring/       # System monitoring and alerting
├── infrastructure/       # External integrations
│   ├── database/         # Database connections and repositories
│   ├── cache/            # Redis caching layer
│   └── external/         # External API integrations
├── repositories/         # Data access layer
└── utils/               # Shared utilities
```

### Running Tests
```bash
# Install development dependencies
pip install -e ".[dev,test]"

# Run all tests
pytest

# Run with coverage
pytest --cov=reskpoints --cov-report=html

# Run specific test categories
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests
pytest -m "not slow"        # Skip slow tests
```

### Code Quality
```bash
# Format code
black reskpoints/ tests/
isort reskpoints/ tests/

# Lint code
flake8 reskpoints/ tests/
mypy reskpoints/

# Run all quality checks
pre-commit run --all-files
```

### Adding New Features

1. **Data Models**: Define Pydantic models in `models/`
2. **API Endpoints**: Add routes in `api/v1/`
3. **Business Logic**: Implement services in `services/`
4. **Data Access**: Create repositories in `repositories/`
5. **Tests**: Add tests in `tests/unit/` and `tests/integration/`

Example - Adding a new metric type:

```python
# models/metrics.py
class CustomMetric(AIMetric):
    custom_field: str
    additional_data: Dict[str, Any]

# api/v1/metrics.py
@router.post("/custom")
async def submit_custom_metric(metric: CustomMetric):
    return await metrics_service.process_custom_metric(metric)

# services/metrics/processor.py
async def process_custom_metric(self, metric: CustomMetric):
    # Business logic implementation
    pass
```

## 🚢 Production Deployment

### Docker Production
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  reskpoints:
    image: reskpoints:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
    restart: unless-stopped
    depends_on:
      - postgres
      - redis
      - timescaledb
```

### Kubernetes Deployment
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: reskpoints
spec:
  replicas: 3
  selector:
    matchLabels:
      app: reskpoints
  template:
    metadata:
      labels:
        app: reskpoints
    spec:
      containers:
      - name: reskpoints
        image: reskpoints:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: reskpoints-secrets
              key: database-url
```

### Scaling Considerations

- **Horizontal Scaling**: Stateless application, scales with load balancers
- **Database**: Use read replicas for analytics queries
- **Cache**: Redis Cluster for high availability
- **Monitoring**: Distributed tracing with Jaeger for multi-instance deployments

## 🔒 Security

### Authentication & Authorization
- **JWT Tokens**: Secure API access with configurable expiration
- **RBAC**: Role-based access control with granular permissions
- **API Keys**: Optional API key authentication for service-to-service

### Data Protection
- **Encryption**: Data encrypted at rest and in transit (TLS 1.3)
- **Input Validation**: Comprehensive request validation and sanitization
- **Audit Logging**: All sensitive operations logged for compliance

### Security Headers
```python
# Automatic security headers
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Quick Contribution Setup
```bash
# Fork the repository and clone
git clone https://github.com/yourusername/ReskPoints.git
cd ReskPoints

# Create a feature branch
git checkout -b feature/your-feature-name

# Setup development environment
./scripts/setup-dev.sh

# Make your changes and add tests
# ... develop ...

# Run quality checks
pre-commit run --all-files
pytest

# Commit and push
git commit -m "feat: add your feature description"
git push origin feature/your-feature-name
```

### Development Guidelines
- **Code Style**: Follow Black formatting and PEP 8
- **Testing**: Maintain >90% test coverage
- **Documentation**: Update docstrings and API documentation
- **Type Safety**: Use type hints for all new code

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Documentation**: [API Docs](http://localhost:8000/docs) (when running)
- **Repository**: [GitHub](https://github.com/Resk-Security/ReskPoints)
- **Issues**: [Bug Reports](https://github.com/Resk-Security/ReskPoints/issues)
- **Security**: [Security Policy](SECURITY.md)

## 🎯 Roadmap

### Current Version (v0.1.0)
- ✅ Core API endpoints and data models
- ✅ Basic monitoring and health checks
- ✅ Docker development environment
- ✅ Authentication framework

### Next Release (v0.2.0)
- 🔄 Database persistence layer
- 🔄 Real-time anomaly detection
- 🔄 Advanced cost analytics
- 🔄 WebSocket real-time updates

### Future Releases
- 📋 Machine learning-based insights
- 📋 Advanced causality analysis
- 📋 Multi-tenant architecture
- 📋 Mobile application support

---

**Built with ❤️ by Resk Security**

For questions or support, please [open an issue](https://github.com/Resk-Security/ReskPoints/issues) or contact us at contact@resk-security.com
