# Telemetry Module Usage Guide

This guide covers how to use, configure, and extend the production telemetry system for the Lead Ignite backend.

---

## Overview
The telemetry system provides distributed tracing, metrics collection, health monitoring, and circuit breaking for FastAPI services. It is built with OpenTelemetry and includes production-grade features like async support, circuit breakers, and Prometheus integration.

---

## Quick Start

```python
from fastapi import FastAPI
from app.core.telemetry.telemetry import setup_telemetry

app = FastAPI()
setup_telemetry(app)  # Initializes all telemetry systems
```

---

## Core Components

- **client.py**: Implements `TelemetryClient` for initializing tracing and metrics, and FastAPI instrumentation. Handles circuit breaking and context management for spans.
- **config.py**: Centralizes environment-specific and production-tuned configuration for OpenTelemetry exporters, batch sizes, sampling, and resource attributes.
- **decorators.py**: Provides decorators for tracing (`@trace_function`), error tracking (`@track_errors`), and performance measurement (`@measure_performance`). All are production-ready with metric integration.
- **health_check.py**: Health check utilities for telemetry, including circuit breaker status and resource checks. Exposes `/health/telemetry` endpoint for FastAPI.
- **telemetry.py**: Entry point for setup and access. Handles FastAPI integration, Prometheus metrics, and health check route registration.

---

## Configuration

Set the following environment variables for production deployments:

- `OTEL_EXPORTER_OTLP_ENDPOINT`: OpenTelemetry Collector endpoint (default: `http://localhost:4317`)
- `OTEL_EXPORTER_OTLP_INSECURE`: Set to `true` for insecure connections
- `SERVICE_NAME`: Service identifier (should match service discovery)
- `SERVICE_VERSION`: Service version (from your CI/CD pipeline or config)
- `ENVIRONMENT`: `production`, `staging`, or `development`
- `ENABLE_PROMETHEUS`: Enable Prometheus metrics (default: `true`)

Fine-tune advanced options in `config.py` for batch sizes, timeouts, and sampling rates.

---

## Usage Patterns

### Tracing & Metrics
- Use `@trace_function` on any function to create a span and record metrics.
- Use `@measure_performance` to track execution time and log slow calls.
- Use `@track_errors` to automatically record exceptions in traces and metrics.

### Manual Spans
```python
from app.core.telemetry.client import TelemetryClient

with TelemetryClient(...).start_span("operation_name") as span:
    # Your code here
    span.set_attribute("key", "value")
```

### Health Checks
- The `/health/telemetry` endpoint returns JSON with health status and circuit breaker state.
- Use `check_telemetry_health()` for programmatic checks.

---

## Best Practices
- Always initialize telemetry at app startup using `setup_telemetry(app)`.
- Use decorators to ensure all critical paths are traced and monitored.
- Tune sampling and batch sizes for high-volume production environments.
- Monitor key metrics: `app.request.count`, `app.request.latency.ms`, `app.error.count`.
- Use circuit breaking to handle exporter outages gracefully.

---

## Extending
- Add new metrics or spans using OpenTelemetry APIs in `client.py` or via decorators.
- Register additional health metrics in `health_check.py` as needed.

---

## References
- See `README.md` for a feature summary and example configuration.
- See `_docs/best_pracices_getting_started.md` and `_docs/best_practices_traces.md` for advanced OpenTelemetry usage and anti-patterns.

---

For further details, consult the code and the `_docs` directory for best practices and advanced patterns.
