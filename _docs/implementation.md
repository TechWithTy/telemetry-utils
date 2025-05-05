# Telemetry Implementation Guide

This document outlines how tracing, metrics, and logs are configured via `TelemetryClient` in `app.core.telemetry.client`.

## 1. Overview

- **Traces**: Collected via OTLP Span Exporter into Grafana Tempo.
- **Metrics**: Exported via OTLP Metric Exporter into Prometheus/Grafana.
- **Logs**: Forwarded through OTLP Log Exporter into Loki + Tempo.

## 2. Initialization

```python
from app.core.telemetry.client import TelemetryClient

# Provide service name and optional version
tel = TelemetryClient(service_name="lead_ignite_backend", service_version="1.0.0")
```

The constructor calls in order:
1. `_initialize_tracing()`
2. `_initialize_metrics()`
3. `_initialize_logging()`

## 3. Configuration

| Env Var                                 | Purpose                              | Default                  |
|-----------------------------------------|--------------------------------------|--------------------------|
| `OTEL_EXPORTER_OTLP_ENDPOINT`           | Trace exporter endpoint              | `http://localhost:4317` |
| `OTEL_EXPORTER_OTLP_METRICS_ENDPOINT`   | Metrics exporter endpoint            | `http://localhost:4317` |
| `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT`      | Log exporter endpoint                | `http://localhost:4317` |
| `OTEL_EXPORTER_OTLP_INSECURE`           | Allow insecure gRPC                  | `false`                  |
| `ENVIRONMENT`                           | Resource attribute                   | `development`           |

## 4. Span Helpers

- `span_pulsar_operation(op, attrs)` → spans named `pulsar.{op}`
- `span_cache_operation(op, attrs)`  → spans named `cache.{op}`
- `span_celery_operation(op, attrs)` → spans named `celery.{op}`

Usage:
```python
with tel.span_celery_operation("execute", {"task_name": name}):
    # task code
```

## 5. FastAPI Auto-Instrumentation

```python
tel.instrument_fastapi(app)
```

Automatically instruments routes and dependencies.

## 6. Log Integration

- A `LoggingHandler` is attached to the root logger, forwarding logs via OTLP Log Exporter to Loki (and Tempo).
- All calls to `logging.getLogger()` propagate through OTLP into Loki.
- To include secure or custom loggers, ensure `propagate = True` or add the handler explicitly.
- Environment variable `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT` controls the Loki endpoint (default `http://localhost:4317`).

Example for secure/custom loggers:
```python
import logging
from opentelemetry.sdk._logs import LoggingHandler

# Create or get a custom logger
secure_logger = logging.getLogger("secure")
# Ensure propagation to root handler
secure_logger.propagate = True
# Optionally set level
secure_logger.setLevel(logging.INFO)
```
This sends `secure_logger` records through the same OTLP pipeline into Loki.
If you disable propagation, attach the handler manually:
```python
handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
secure_logger.addHandler(handler)
```

## 7. Shutdown

```python
tel.shutdown()
```

Closes exporters and flushes all pending spans, metrics, and logs.
