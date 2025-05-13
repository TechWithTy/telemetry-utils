# Production Telemetry Module

**Production-ready Python/FastAPI Telemetry, Tracing, and Metrics Suite**

This module provides distributed tracing, metrics, and health monitoring for Python microservices using OpenTelemetry and best-in-class async patterns.

---

## 📁 Folder Structure & Conventions

```
telemetry/
├── _docs/           # Markdown docs, best practices, diagrams, usage
├── _tests/          # Unit/integration tests for all core logic
├── config.py        # Singleton config (class-based, imports from global settings)
├── docker/          # Dockerfile, docker-compose, telemetry configs, .env.example
├── models/          # Pydantic models or telemetry schemas
├── exceptions/      # Custom exceptions for telemetry
├── <core>.py        # Main implementation (client.py, decorators.py, health_check.py, telemetry.py, etc.)
├── README.md        # Main readme (this file)
```

- **_docs/**: All documentation, diagrams, and best practices for this module.
- **_tests/**: All tests for this module, including integration, async, and health checks.
- **config.py**: Singleton config pattern, imports from global settings, exposes all constants for this module.
- **docker/**: Containerization assets (Dockerfile, docker-compose, telemetry configs, .env.example, etc).
- **models/**: Pydantic models or schemas for telemetry/tracing payloads.
- **exceptions/**: Custom exception classes for robust error handling.
- **<core>.py**: Main implementation modules (e.g., client.py, decorators.py, health_check.py, telemetry.py).

---

## 🏗️ Singleton & Config Pattern
- Use a single class (e.g., `TelemetryConfig`) in `config.py` to centralize all env, exporter, and integration settings.
- Import from global settings to avoid duplication and ensure DRY config.
- Document all config keys in `_docs/usage.md` and in this README.

---

## Features
- **Distributed Tracing**: End-to-end request tracking
- **Metrics Collection**: Performance and error metrics
- **Health Monitoring**: `/health/telemetry` endpoint
- **Circuit Breaking**: Automatic fallback during outages
- **Async Support**: Non-blocking operations

## Usage
```python
from fastapi import FastAPI
from .telemetry import setup_telemetry

app = FastAPI()
setup_telemetry(app)  # Initializes all telemetry systems
```

## Configuration
Set these environment variables:
- `OTEL_EXPORTER_OTLP_ENDPOINT`: Collector endpoint
- `SERVICE_NAME`: Service identifier
- `SERVICE_VERSION`: Service version

## Monitoring
Key metrics:
- `app.request.count`: Total requests
- `app.request.latency.ms`: Response times
- `app.error.count`: Error rates

## Health Checks
Endpoint: `GET /health/telemetry`

Returns:
```json
{
  "status": "healthy | degraded | unhealthy",
  "details": {
    "circuit_breaker": "open | closed"
  }
}
```

## Decorators
- `@trace_function`: Request tracing
- `@track_errors`: Error logging
- `@measure_performance`: Performance metrics
