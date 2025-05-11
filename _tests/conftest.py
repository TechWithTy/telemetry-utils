import pytest
import subprocess
import requests
import time
import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry._logs import set_logger_provider
import opentelemetry.metrics as metrics


# ! This fixture ensures the OpenTelemetry Collector is running before any tests execute.
@pytest.fixture(scope="session", autouse=True)
def otel_collector():
    """
    Ensure OpenTelemetry Collector is running for tests. If not, start via Docker Compose.
    """
    # * Use the Prometheus metrics endpoint for health checking, as /health is not always present on 4318
    # * Try both 127.0.0.1 and localhost for Docker/Windows compatibility
    # * Use correct port (8899) for Prometheus metrics, and add /health as fallback
    otel_urls = [
        os.environ.get("OTEL_COLLECTOR_HEALTHCHECK_URL", "http://127.0.0.1:8899/metrics"),
        "http://localhost:8899/metrics",
        "http://127.0.0.1:13133/health",
        "http://localhost:13133/health"
    ]
    compose_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docker"))
    compose_file = os.path.join(compose_dir, "docker-compose.otel.local.yml")
    timeout = 30  # seconds
    interval = 2  # seconds

    def is_otel_up():
        for url in otel_urls:
            try:
                resp = requests.get(url, timeout=2)
                # * Accept Prometheus metrics endpoint (text) or health endpoint (JSON)
                if resp.status_code == 200:
                    # Check for health endpoint JSON
                    if url.endswith("/health"):
                        try:
                            data = resp.json()
                            if data.get("status") == "Server available":
                                return True
                        except Exception:
                            continue
                    else:
                        # Assume Prometheus metrics endpoint returns 200 OK
                        return True
            except Exception:
                continue
        return False

    if not is_otel_up():
        # * Start the OTEL Collector via docker-compose
        try:
            subprocess.run([
                "docker-compose", "-f", compose_file, "up", "-d"
            ], cwd=compose_dir, check=True)
        except Exception as e:
            pytest.exit(f"! Failed to start OpenTelemetry Collector: {e}")

        # * Wait for OTEL Collector to be healthy
        start = time.time()
        while time.time() - start < timeout:
            if is_otel_up():
                break
            time.sleep(interval)
        else:
            pytest.exit("! OpenTelemetry Collector failed to start within timeout.")

    yield
    # todo: Optionally stop the collector after tests (if desired)

# * NOTE: Removed global OpenTelemetry provider resets to avoid ProxyTracerProvider errors.
# * Test isolation is now handled by patching providers in each test file (see test_client.py).
# * Only the otel_collector fixture remains here for collector health.
@pytest.fixture(autouse=True)
def reset_telemetry():
    """Reset telemetry state between tests"""
    trace._TRACER_PROVIDER = None
    yield
    trace._TRACER_PROVIDER = None
