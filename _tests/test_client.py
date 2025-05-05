from unittest.mock import patch

import pytest

from ..client import TelemetryClient


@pytest.fixture
def mock_tracer_provider():
    with patch('opentelemetry.sdk.trace.TracerProvider') as mock:
        yield mock

@pytest.fixture
def mock_meter_provider():
    with patch('opentelemetry.sdk.metrics.MeterProvider') as mock:
        yield mock

def test_client_initialization(mock_tracer_provider, mock_meter_provider):
    """Test that client properly initializes tracing and metrics"""
    client = TelemetryClient("test-service", "1.0.0")
    
    assert mock_tracer_provider.called
    assert mock_meter_provider.called
    assert client.service_name == "test-service"
    assert client.service_version == "1.0.0"

def test_shutdown(mock_tracer_provider, mock_meter_provider):
    """Test that shutdown properly cleans up providers"""
    client = TelemetryClient("test-service")
    client.shutdown()
    
    assert mock_tracer_provider.return_value.shutdown.called
    assert mock_meter_provider.return_value.shutdown.called
