from unittest.mock import patch

import pytest

from ..client import TelemetryClient


@pytest.fixture
def mock_tracer_provider():
    with patch('opentelemetry.sdk.trace.TracerProvider') as mock:
        with patch('opentelemetry.trace.set_tracer_provider') as set_provider:
            yield mock

@pytest.fixture
def mock_meter_provider():
    with patch('opentelemetry.sdk.metrics.MeterProvider') as mock:
        with patch('opentelemetry.metrics.set_meter_provider') as set_provider:
            yield mock

def test_client_initialization(mock_tracer_provider, mock_meter_provider):
    """Test that client properly initializes tracing and metrics"""
    client = TelemetryClient("test-service", "1.0.0")
    
    assert mock_tracer_provider.called, "TracerProvider was not called during TelemetryClient init"
    assert mock_meter_provider.called, "MeterProvider was not called during TelemetryClient init"
    assert client.service_name == "test-service", f"Expected service_name 'test-service', got: {client.service_name}"
    assert client.service_version == "1.0.0", f"Expected version '1.0.0', got: {client.service_version}"

def test_shutdown(mock_tracer_provider, mock_meter_provider):
    """Test that shutdown properly cleans up providers"""
    client = TelemetryClient("test-service")
    client.shutdown()
    
    assert mock_tracer_provider.return_value.shutdown.called, "TracerProvider.shutdown was not called"
    assert mock_meter_provider.return_value.shutdown.called, "MeterProvider.shutdown was not called"

# * Additional test to verify collector health endpoint with Docker/Windows fallback
import requests
import pytest

def test_collector_health_endpoint():
    """Test collector health endpoint on both 127.0.0.1 and localhost (Docker/Windows compatibility)."""
    urls = ["http://127.0.0.1:13133/health", "http://localhost:13133/health"]
    healthy = False
    for url in urls:
        try:
            resp = requests.get(url, timeout=2)
            if resp.status_code == 200 and resp.json().get("status") == "Server available":
                healthy = True
                break
        except Exception:
            continue
    assert healthy, (
        "OTel collector health endpoint not available on any host alias. URLs checked: "
        f"{urls}. If running in CI or Docker, ensure OTEL Collector is up."
    )

