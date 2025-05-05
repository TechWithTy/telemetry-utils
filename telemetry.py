# c:\Users\tyriq\Documents\Github\lead_ignite_backend_3.0\backend\app\core\telemetry\telemetry.py
import os
from typing import Optional

from fastapi import APIRouter, FastAPI

from .client import TelemetryClient
from .decorators import measure_performance, trace_function, track_errors
from .health_check import health_response

# Initialize at module level for easy access
telemetry_client: Optional[TelemetryClient] = None


def setup_telemetry(app: FastAPI) -> TelemetryClient:
    """
    Production-ready telemetry setup with health checks and Prometheus integration.

    Args:
        app: FastAPI application instance

    Returns:
        Configured TelemetryClient instance
    """
    global telemetry_client

    # Initialize OpenTelemetry client
    telemetry_client = TelemetryClient(
        service_name=os.getenv("SERVICE_NAME", "lead-ignite-backend"),
        service_version=os.getenv("SERVICE_VERSION", "1.0.0"),
    )

    # Instrument FastAPI with OpenTelemetry
    telemetry_client.instrument_fastapi(app)
    
    # Add Prometheus instrumentation if enabled (will use same prometheus_client)
    if os.getenv("ENABLE_PROMETHEUS", "true").lower() == "true":
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


@trace_function(attributes={"component": "telemetry"})
def shutdown_telemetry():
    """Properly shutdown telemetry providers."""
    if telemetry_client is not None:
        telemetry_client.shutdown()


instrument = trace_function
monitor_errors = track_errors
monitor_performance = measure_performance
