from unittest.mock import patch

import pytest

from ..client import TelemetryClient


@pytest.fixture
def mock_tracer_provider():
    # * Disable SSL verification for OTLP exporter in local/dev testing
    # import ssl
    # ssl._create_default_https_context = ssl._create_unverified_context
    with patch('app.core.telemetry.client.TracerProvider') as mock_class, \
         patch('opentelemetry.trace.set_tracer_provider') as set_provider, \
         patch('opentelemetry.trace.get_tracer_provider') as get_provider:
        mock_instance = MagicMock()
        mock_instance.add_span_processor = MagicMock()
        mock_instance.shutdown = MagicMock()
        get_provider.return_value = mock_instance
        yield mock_class
@pytest.fixture
def mock_meter_provider():
    with patch('app.core.telemetry.client.MeterProvider') as mock:
        with patch('opentelemetry.metrics.set_meter_provider') as set_provider:
            yield mock

from unittest.mock import MagicMock


def test_client_initialization(mock_tracer_provider, mock_meter_provider):
    client = TelemetryClient("test-service", "1.0.0")
    assert mock_tracer_provider.called, "TracerProvider was not called during TelemetryClient init"
    assert mock_meter_provider.called, "MeterProvider was not called during TelemetryClient init"
    assert client.service_name == "test-service", f"Expected service_name 'test-service', got: {client.service_name}"
    assert client.service_version == "1.0.0", f"Expected version '1.0.0', got: {client.service_version}"
    """Test that client properly initializes tracing and metrics"""
    # Removed duplicate code block


def test_shutdown(mock_tracer_provider, mock_meter_provider):
    with patch('opentelemetry.metrics.get_meter_provider') as get_meter_provider:
        mock_meter_provider_inst = MagicMock()
        get_meter_provider.return_value = mock_meter_provider_inst
        mock_meter_provider_inst.shutdown = MagicMock()
        # Patch get_tracer_provider to return the same mock as mock_tracer_provider.return_value
        with patch('opentelemetry.trace.get_tracer_provider', return_value=mock_tracer_provider.return_value):
            client = TelemetryClient("test-service")
            client.shutdown()
            # TracerProvider shutdown is handled by the fixture mock
            mock_tracer_provider.return_value.shutdown.assert_called_once()
        assert mock_meter_provider_inst.shutdown.called, "MeterProvider.shutdown was not called"
    # Only test shutdown within the patch context above to avoid AttributeError on _ProxyMeterProvider.
    # The duplicate call below is removed.
    #
    # assert mock_tracer_provider.return_value.shutdown.called, "TracerProvider.shutdown was not called"
    # assert mock_meter_provider.return_value.shutdown.called, "MeterProvider.shutdown was not called"

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

