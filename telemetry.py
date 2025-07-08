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
    Optimized for Grafana Cloud Tempo with fixes for service name and trace gaps.

    Args:
        app: FastAPI application instance

    Returns:
        Configured TelemetryClient instance
    """
    global telemetry_client

    # Get service configuration with explicit defaults
    service_name = os.getenv("SERVICE_NAME", "fastapi-connect-backend")
    service_version = os.getenv("SERVICE_VERSION", "1.0.0")
    environment = os.getenv("ENVIRONMENT", "production")
    
    # Create unique instance ID for better tracing
    import uuid
    instance_id = f"{service_name}-{uuid.uuid4().hex[:8]}"
    
    print(f"[TELEMETRY] Initializing telemetry for {service_name} (instance: {instance_id})")

    # Initialize OpenTelemetry client with explicit configuration
    telemetry_client = TelemetryClient(
        service_name=service_name,
        service_version=service_version,
        auto_init=False,  # We'll configure exporters manually
        instance_id=instance_id,
        environment=environment
    )

    # Configure OTLP exporter for Grafana Cloud Tempo
    if os.getenv("USE_MANAGED_SERVICES") == "true":
        print("[INFO] Configuring Grafana Cloud Tempo integration", flush=True)
        # Grafana Cloud configuration
        otlp_endpoint = os.getenv("TEMPO_EXPORTER_ENDPOINT")
        tempo_username = os.getenv("TEMPO_USERNAME")  
        tempo_api_key = os.getenv("TEMPO_API_KEY")
        
        print(f"[DEBUG] TEMPO_EXPORTER_ENDPOINT: {otlp_endpoint}", flush=True)
        print(f"[DEBUG] TEMPO_USERNAME: {tempo_username}", flush=True)
        print(f"[DEBUG] TEMPO_API_KEY: {'✓' if tempo_api_key else '✗'}", flush=True)
        
        if not otlp_endpoint or not tempo_username or not tempo_api_key:
            print("[WARNING] Grafana Cloud credentials not properly configured", flush=True)
            print("  TEMPO_EXPORTER_ENDPOINT:", "✓" if otlp_endpoint else "✗")
            print("  TEMPO_USERNAME:", "✓" if tempo_username else "✗")
            print("  TEMPO_API_KEY:", "✓" if tempo_api_key else "✗")
        
        # Use basic authentication for Grafana Cloud Tempo (gRPC metadata format)
        import base64
        credentials = f"{tempo_username}:{tempo_api_key}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        # gRPC uses metadata, not headers - and expects key-value tuples
        headers = (
            ("authorization", f"Basic {encoded_credentials}"),
        )
        
        span_exporter = OTLPSpanExporter(
            endpoint=otlp_endpoint,
            headers=headers,
            timeout=30,
            insecure=False  # Use secure connection for Grafana Cloud
        )
        
        # Also configure metrics exporter for Grafana Cloud
        metrics_endpoint = otlp_endpoint.replace("/api/traces", "/api/push")
        print(f"[DEBUG] Metrics endpoint: {metrics_endpoint}", flush=True)
        metric_exporter = OTLPMetricExporter(
            endpoint=metrics_endpoint,
            headers=headers,
            timeout=30,
            insecure=False  # Use secure connection for Grafana Cloud
        )
        
        print("[INFO] Grafana Cloud exporters configured with Basic Auth", flush=True)
    else:
        print("[INFO] Using local Tempo setup", flush=True)
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
