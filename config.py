from app.core.config import settings
from typing import Optional

# Sensitive settings (should be environment-specific)
OTEL_EXPORTER_OTLP_ENDPOINT: str = getattr(
    settings, "OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"
)
OTEL_EXPORTER_OTLP_INSECURE: bool = bool(
    getattr(settings, "OTEL_EXPORTER_OTLP_INSECURE", False)
)

# Production recommendations:
OTEL_SERVICE_NAME: str = "lead_ignite_backend"  # Should match service discovery
OTEL_SERVICE_VERSION: str = settings.APP_VERSION  # Use from your app config
OTEL_DEPLOYMENT_ENVIRONMENT: str = settings.ENVIRONMENT  # prod/stage/dev

# Performance tuning for production:
OTEL_BSP_MAX_EXPORT_BATCH_SIZE: int = 512  # Default is good
OTEL_BSP_SCHEDULE_DELAY: int = 5000  # ms (5s - conservative for production)
OTEL_BSP_EXPORT_TIMEOUT: int = 30000  # ms (30s - conservative)

# Sampling configuration (adjust based on volume):
OTEL_TRACE_SAMPLER: str = "parentbased_always_on"  # Good default
OTEL_SAMPLING_RATE: float = (
    0.1 if settings.ENVIRONMENT == "production" else 1.0
)  # Sample 10% in prod

# Additional production recommendations:
OTEL_PROPAGATORS: str = "tracecontext,baggage"  # Ensure context propagation
OTEL_RESOURCE_ATTRIBUTES: str | None = getattr(
    settings, "OTEL_RESOURCE_ATTRIBUTES", None
)  # For additional metadata
