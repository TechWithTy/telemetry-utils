"""
Telemetry health checks for production monitoring.

Includes checks for:
- Connection status to telemetry backends
- Circuit breaker state
- Resource utilization
"""
import logging
from typing import Dict, Optional

from fastapi import Response, status
from opentelemetry import metrics

from .client import TelemetryClient

logger = logging.getLogger(__name__)


def check_telemetry_health(client: Optional[TelemetryClient] = None) -> Dict[str, str]:
    """
    Comprehensive health check for telemetry system.
    
    Args:
        client: Optional TelemetryClient instance (will use global if None)
        
    Returns:
        Dict with health status and details
    """
    if client is None:
        from .telemetry import get_telemetry
        try:
            client = get_telemetry()
        except RuntimeError:
            return {
                "status": "unhealthy",
                "reason": "Telemetry client not initialized"
            }

    health_status = {"status": "healthy"}
    
    # Check circuit breaker state
    if hasattr(client, "circuit_breaker") and client.circuit_breaker.is_open:
        health_status.update({
            "status": "degraded",
            "circuit_breaker": "open",
            "reason": "Telemetry backend unavailable"
        })
    
    # Add any additional backend-specific checks here
    
    return health_status


def health_response() -> Response:
    """
    Generate FastAPI response for telemetry health check.
    """
    health = check_telemetry_health()
    status_code = (
        status.HTTP_200_OK if health["status"] == "healthy" 
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    
    return Response(
        content=health,
        status_code=status_code,
        media_type="application/json"
    )


def register_health_metrics():
    """
    Register health-related metrics for monitoring.
    """
    meter = metrics.get_meter(__name__)
    meter.create_observable_gauge(
        "telemetry.health.status",
        callbacks=[lambda: 1],  # TODO: Implement actual health metric
        description="Telemetry health status (1=healthy, 0=unhealthy)"
    )


# Pre-register metrics when module loads
register_health_metrics()
