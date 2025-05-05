# Production Telemetry Module

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
