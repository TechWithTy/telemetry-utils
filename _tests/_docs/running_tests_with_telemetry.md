# Running Telemetry Tests: Best Practices & Troubleshooting

This guide explains how to run and debug tests for the telemetry system in this codebase, ensuring robust, isolated, and reproducible results.

---

## 1. **Requirements**
- **Docker** (for local OpenTelemetry Collector)
- **Poetry** (for Python dependency management)
- **Python 3.12+**

---

## 2. **Start the OpenTelemetry Collector**
Telemetry tests require a running OTEL Collector. Start it with:

```sh
cd backend/app/core/telemetry/docker
# Start the collector in the background
docker-compose -f docker-compose.otel.local.yml up -d
```
- Wait until you see `Everything is ready. Begin running and processing data.` in the logs:
  ```sh
  docker-compose -f docker-compose.otel.local.yml logs
  ```

---

## 3. **Run the Tests**
From the project root or backend directory:

```sh
poetry run pytest app/core/telemetry/_tests/ -s
```

- The `-s` flag shows print/debug output.
- All health check, client, and decorator tests should pass if the collector is running and all dependencies are installed.

---

## 4. **Test Isolation & Mocking**
- **Provider resets**: Do NOT globally reset OpenTelemetry providers in fixtures. Instead, tests patch provider methods using `unittest.mock.patch` for isolation.
- **CI/CD**: The collector must be running in CI for tests to pass. Use a service container or similar mechanism.
- **Troubleshooting**:
  - If you see `ProxyTracerProvider` or `add_span_processor` errors, check that provider patching is in place and no global resets occur.
  - If health check tests fail, ensure the collector is accessible at `http://127.0.0.1:13133/health`.
  - Use `docker-compose logs` for collector troubleshooting.

---

## 5. **Environment Variables**
Set these as needed for local/CI runs:
- `OTEL_EXPORTER_OTLP_ENDPOINT` (default: `http://localhost:4317`)
- `OTEL_EXPORTER_OTLP_INSECURE` (default: `true` for local)
- `SERVICE_NAME`, `SERVICE_VERSION`, `ENVIRONMENT`

---

## 6. **Additional Tips**
- Review `test_client.py` and `conftest.py` for up-to-date patching patterns.
- Use the `_docs/otel_debugging_and_testing.md` for advanced debugging scenarios.
- For more, see: https://opentelemetry.io/docs/instrumentation/python/

---

*Last updated: 2025-05-11*
