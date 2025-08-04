"""
Telemetry health checks for production monitoring.

Includes checks for:
- Connection status to telemetry backends
- Circuit breaker state
- Resource utilization
"""
import logging
from typing import Optional

from fastapi import Response, status
from fastapi.responses import JSONResponse
from opentelemetry import metrics

from .client import TelemetryClient

logger = logging.getLogger(__name__)


def check_telemetry_health(client: Optional[TelemetryClient] = None) -> dict[str, str]:
    """
    Comprehensive health check for telemetry system.
    
    Args:
        client: Optional TelemetryClient instance (will use global if None)
        
    Returns:
        dict with health status and details
    """
    # Import here to avoid circular import
    if client is None:
        from .telemetry import get_telemetry
        client = get_telemetry()
        
    # If still None, telemetry is not initialized
    if client is None:
        logger.warning("Telemetry health check called but client is not initialized")
        return {"status": "unhealthy", "reason": "Telemetry client not initialized"}

    health_status = {"status": "healthy", "circuit_breaker": "closed"}
    
    # Check circuit breaker state
    if hasattr(client, "circuit_breaker") and client.circuit_breaker.is_open:
        health_status.update({
            "status": "degraded",
            "circuit_breaker": "open",
            "reason": "Telemetry backend unavailable"
        })
    
    # Check exporter health if available
    if hasattr(client, "exporters") and client.exporters:
        exporters_status = {}
        all_healthy = True
        
        for name, exporter in client.exporters.items():
            if hasattr(exporter, "is_healthy") and callable(exporter.is_healthy):
                try:
                    is_healthy = exporter.is_healthy()
                    exporters_status[name] = "healthy" if is_healthy else "unhealthy"
                    all_healthy = all_healthy and is_healthy
                except Exception as e:
                    logger.exception(f"Error checking health of exporter {name}")
                    exporters_status[name] = f"error: {str(e)}"
                    all_healthy = False
        
        if not all_healthy:
            health_status["status"] = "degraded"
            health_status["reason"] = "One or more exporters unhealthy"
        
        health_status["exporters"] = exporters_status
    
    return health_status


def health_response() -> Response:
    """
    Generate FastAPI response for telemetry health check.
    """
    from .telemetry import get_telemetry
    
    # Use the global telemetry client
    client = get_telemetry()
    health = check_telemetry_health(client)
    
    # Determine status code based on health status
    status_code = status.HTTP_200_OK
    if health["status"] == "unhealthy":
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif health["status"] == "degraded":
        status_code = status.HTTP_200_OK  # Degraded is still 200 but with warning content
    
    return JSONResponse(
        content=health,
        status_code=status_code,
    )


def get_health_status_numeric(client: Optional[TelemetryClient] = None) -> float:
    """
    Convert health status to a numeric value for metrics.
    
    Returns:
        2.0 for healthy
        1.0 for degraded
        0.0 for unhealthy/uninitialized
    """
    health = check_telemetry_health(client)
    status = health.get("status", "unhealthy")
    
    if status == "healthy":
        return 2.0
    elif status == "degraded":
        return 1.0
    else:
        return 0.0


def register_health_metrics():
    """
    Register health-related metrics for monitoring.
    """
    meter = metrics.get_meter(__name__)
    
    # Define callback that returns a simple numeric value
    def health_callback(_):
        """Returns current telemetry health status as a numeric value."""
        try:
            # Import here to avoid circular import
            from .telemetry import get_telemetry
            
            # Get the global telemetry client
            client = get_telemetry()
            status_value = get_health_status_numeric(client)
            
            # Return a simple numeric value (not a tuple)
            return status_value
        except Exception as e:
            logging.exception("Error in health metrics callback")
            return 0.0  # Return unhealthy on error
    
    # Create observable gauge with callbacks parameter (list of callbacks)
    meter.create_observable_gauge(
        name="telemetry_health_status",
        description="Telemetry health status (2=healthy, 1=degraded, 0=unhealthy)",
        unit="status",
        callbacks=[health_callback]  # Use callbacks (list) instead of callback (single function)
    )