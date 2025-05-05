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
    assert result["status"] == "healthy"


def test_health_check_degraded():
    """Test health check with open circuit breaker."""
    mock_client = MagicMock(spec=TelemetryClient)
    mock_client.circuit_breaker.is_open = True
    
    result = check_telemetry_health(mock_client)
    assert result["status"] == "degraded"
    assert "circuit_breaker" in result


def test_health_check_uninitialized():
    """Test health check when telemetry is not initialized."""
    with patch("app.core.telemetry.health_check.get_telemetry") as mock_get:
        mock_get.side_effect = RuntimeError("Not initialized")
        result = check_telemetry_health()
        assert result["status"] == "unhealthy"
        assert "not initialized" in result["reason"].lower()


def test_health_response_healthy():
    """Test FastAPI response generation for healthy state."""
    with patch("app.core.telemetry.health_check.check_telemetry_health") as mock_check:
        mock_check.return_value = {"status": "healthy"}
        response = health_response()
        assert response.status_code == status.HTTP_200_OK


def test_health_response_unhealthy():
    """Test FastAPI response generation for unhealthy state."""
    with patch("app.core.telemetry.health_check.check_telemetry_health") as mock_check:
        mock_check.return_value = {"status": "unhealthy"}
        response = health_response()
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


# Integration test example (would need proper test client setup)
@pytest.mark.integration
def test_health_check_integration(telemetry_client):
    """Integration test with actual telemetry client."""
    result = check_telemetry_health(telemetry_client)
    assert "status" in result
    assert result["status"] in ["healthy", "degraded"]
