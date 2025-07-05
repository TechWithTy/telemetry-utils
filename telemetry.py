# c:\Users\tyriq\Documents\Github\lead_ignite_backend_3.0\backend\app\core\telemetry\telemetry.py
import os
from typing import Optional

from fastapi import APIRouter, FastAPI
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

from .client import TelemetryClient
from .decorators import measure_performance, trace_function, track_errors
from .health_check import health_response

# Initialize at module level for easy access
telemetry_client: Optional[TelemetryClient] = None


def setup_telemetry(app: FastAPI) -> TelemetryClient:
    """
    Production-ready telemetry setup with health checks and Prometheus integration.
    Optimized for Grafana Cloud Tempo.

    Args:
        app: FastAPI application instance

    Returns:
        Configured TelemetryClient instance
    """
    global telemetry_client

    # Initialize OpenTelemetry client (without auto-init for custom configuration)
    telemetry_client = TelemetryClient(
        service_name=os.getenv("SERVICE_NAME", "fastapi-connect-backend"),
        service_version=os.getenv("SERVICE_VERSION", "1.0.0"),
        auto_init=False  # We'll configure exporters manually
    )

    # Configure OTLP exporter for Grafana Cloud Tempo
    if os.getenv("USE_MANAGED_SERVICES") == "true":
        # Grafana Cloud configuration
        otlp_endpoint = os.getenv("TEMPO_EXPORTER_ENDPOINT")
        grafana_api_key = os.getenv("GRAFANA_CLOUD_API_KEY")
        
        if not otlp_endpoint or not grafana_api_key:
            print("[WARNING] Grafana Cloud credentials not properly configured", flush=True)
            print("  TEMPO_EXPORTER_ENDPOINT:", "✓" if otlp_endpoint else "✗")
            print("  GRAFANA_CLOUD_API_KEY:", "✓" if grafana_api_key else "✗")
        
        headers = {
            "Authorization": f"Bearer {grafana_api_key}"
        }
        
        span_exporter = OTLPSpanExporter(
            endpoint=otlp_endpoint,
            headers=headers,
            timeout=30  # 30 second timeout for cloud
        )
        
        # Also configure metrics exporter for Grafana Cloud
        metrics_endpoint = otlp_endpoint.replace("/api/traces", "/api/push")
        metric_exporter = OTLPMetricExporter(
            endpoint=metrics_endpoint,
            headers=headers,
            timeout=30
        )
    else:
        # Local Tempo setup
        local_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        span_exporter = OTLPSpanExporter(endpoint=local_endpoint)
        metric_exporter = OTLPMetricExporter(endpoint=local_endpoint)
    
    # Configure telemetry client with the exporters
    telemetry_client.configure_exporters(span_exporter, metric_exporter)
    
    # Instrument FastAPI with OpenTelemetry
    telemetry_client.instrument_fastapi(app)
    
    # Add Prometheus instrumentation if enabled (will use same prometheus_client)
    if os.getenv("ENABLE_PROMETHEUS", "true").lower() == "true":
        try:
            from prometheus_fastapi_instrumentator import Instrumentator
            
            # Create instrumentator with custom metrics
            instrumentator = Instrumentator(
                should_group_status_codes=True,
                should_ignore_untemplated=True
            )
            
            # Add default metrics
            instrumentator.instrument(app)
            
            # Keep existing prometheus-client metrics
            @app.on_event("startup")
            async def expose_metrics():
                instrumentator.expose(app)
        except ImportError:
            print("[WARNING] prometheus_fastapi_instrumentator not available", flush=True)
    
    # Register health check endpoint
    health_router = APIRouter()
    health_router.add_api_route(
        "/health/telemetry",
        health_response,
        methods=["GET"],
        tags=["monitoring"],
        summary="Telemetry system health",
        response_description="Telemetry health status",
    )
    app.include_router(health_router)

    return telemetry_client


def get_telemetry() -> TelemetryClient:
    """
    Get the configured telemetry client instance.

    Raises:
        RuntimeError: If telemetry hasn't been initialized
    """
    if telemetry_client is None:
        raise RuntimeError("Telemetry not initialized. Call setup_telemetry() first.")
    return telemetry_client


@trace_function("shutdown_telemetry", attributes={"component": "telemetry"})
def shutdown_telemetry():
    """Properly shutdown telemetry providers."""
    if telemetry_client is not None:
        telemetry_client.shutdown()


instrument = trace_function
monitor_errors = track_errors
monitor_performance = measure_performance
