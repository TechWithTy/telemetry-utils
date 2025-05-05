from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI

from ..telemetry import get_telemetry, setup_telemetry, shutdown_telemetry


@pytest.fixture
def mock_app():
    """Fixture providing a FastAPI test application."""
    app = FastAPI()
    return app


def test_setup_telemetry(mock_app):
    """Verify telemetry setup properly instruments FastAPI."""
    with patch('app.core.telemetry.client.TelemetryClient') as mock_client:
        client = setup_telemetry(mock_app)
        assert mock_client.called
        assert mock_client.return_value.instrument_fastapi.called
        assert mock_client.return_value == client


def test_get_telemetry_before_setup():
    """Verify proper error when getting telemetry before setup."""
    with pytest.raises(RuntimeError, match="Telemetry not initialized"):
        get_telemetry()


def test_shutdown_telemetry():
    """Verify telemetry shutdown calls client shutdown."""
    mock_client = MagicMock()
    with patch('app.core.telemetry._TELEMETRY_CLIENT', mock_client):
        shutdown_telemetry()
        mock_client.shutdown.assert_called_once()
