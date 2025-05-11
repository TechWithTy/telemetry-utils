"""
Comprehensive tests for telemetry health checks.
"""
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status

from ..client import TelemetryClient
from ..health_check import check_telemetry_health, health_response


def test_health_check_healthy():
    """Test health check with healthy client."""
    mock_client = MagicMock(spec=TelemetryClient)
    mock_client.circuit_breaker.is_open = False
    
    result = check_telemetry_health(mock_client)
    assert result["status"] == "healthy", f"Expected healthy, got: {result}"


def test_health_check_degraded():
    """Test health check with open circuit breaker."""
    mock_client = MagicMock(spec=TelemetryClient)
    mock_client.circuit_breaker.is_open = True
    
    result = check_telemetry_health(mock_client)
    assert result["status"] == "degraded", f"Expected degraded, got: {result}"
    assert "circuit_breaker" in result, f"circuit_breaker key missing in result: {result}"


def test_health_check_uninitialized():
    """Test health check when telemetry is not initialized."""
    with patch("app.core.telemetry.health_check.get_telemetry") as mock_get:
        mock_get.side_effect = RuntimeError("Not initialized")
        result = check_telemetry_health()
        assert result["status"] == "unhealthy", f"Expected unhealthy, got: {result}"
        assert "not initialized" in result["reason"].lower(), f"Reason missing 'not initialized': {result['reason']}"


def test_health_response_healthy():
    """Test FastAPI response generation for healthy state."""
    with patch("app.core.telemetry.health_check.check_telemetry_health") as mock_check:
        mock_check.return_value = {"status": "healthy"}
        response = health_response()
        assert response.status_code == status.HTTP_200_OK, f"Expected 200 OK, got: {response.status_code}"


def test_health_response_unhealthy():
    """Test FastAPI response generation for unhealthy state."""
    with patch("app.core.telemetry.health_check.check_telemetry_health") as mock_check:
        mock_check.return_value = {"status": "unhealthy"}
        response = health_response()
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE, f"Expected 503, got: {response.status_code}"


# Integration test example (would need proper test client setup)
@pytest.mark.integration
# * This test demonstrates how to check the collector health endpoint using both 127.0.0.1 and localhost for Docker/Windows compatibility.
def test_health_check_integration(telemetry_client):
    """Integration test with actual telemetry client and HTTP health endpoint."""
    import requests
    urls = [
        "http://127.0.0.1:13133/health",
        "http://localhost:13133/health"
    ]
    healthy = False
    for url in urls:
        try:
            resp = requests.get(url, timeout=2)
            if resp.status_code == 200 and resp.json().get("status") == "Server available":
                healthy = True
                break
        except Exception:
            continue
    assert healthy, "OTel collector health endpoint not available on any host alias"
    # Also check internal health logic
    result = check_telemetry_health(telemetry_client)
    assert result["status"] in ["healthy", "degraded"]
