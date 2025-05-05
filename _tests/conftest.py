import pytest
from opentelemetry import trace


@pytest.fixture(autouse=True)
def reset_telemetry():
    """Reset telemetry state between tests"""
    trace._TRACER_PROVIDER = None
    yield
    trace._TRACER_PROVIDER = None
