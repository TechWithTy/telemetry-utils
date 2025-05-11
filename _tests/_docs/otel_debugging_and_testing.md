# OpenTelemetry Collector Debugging & Testing Guide

---
## Collector Health Endpoint Best Practices

- The Collector's built-in `/health` endpoint is only available if the `health_check` extension is enabled and port **13133** is mapped in Docker Compose.
- On Windows with Docker Desktop, `curl http://localhost:13133/health` may fail, but `curl http://127.0.0.1:13133/health` usually works—always test both.
- The OTLP HTTP endpoint (`4318`) does **not** provide a `/health` endpoint by default; a 404 or connection reset is expected unless the health extension is enabled.
- For Docker network debugging, use a sidecar like `busybox` to verify connectivity: `docker run --rm --network app-network busybox wget -qO- http://otel-collector-minimal:13133/health`.
- For CI and test reliability, prefer checking the Prometheus `/metrics` endpoint (default port **8889**) or using internal health-check logic (e.g., `check_telemetry_health()` from `health_check.py`).
- If you need to expose `/health` externally, ensure firewall rules allow the port and that Docker Desktop is restarted after config changes.

---
## Test and Troubleshooting Checklist

- [x] Enable the `health_check` extension and map port 13133 in Docker Compose for HTTP health checks.
- [x] Use `curl http://127.0.0.1:13133/health` on Windows if `localhost` fails.
- [x] For tests, use the Prometheus `/metrics` endpoint or internal health-check logic for most reliable results.
- [x] Use a sidecar container (`busybox`, `curl`, etc.) to test network connectivity from within Docker.
- [x] Restart Docker Desktop after making Compose or config changes to ensure port mappings are refreshed.
- [x] Temporarily disable firewall/antivirus to rule out host port blocking.
- [x] If the container has no shell, use a networked debug container for troubleshooting.

---


## Debugging Methods We Tried

1. **Checked for Port Conflicts**
   - Used `netstat -aon | findstr :<port>` to verify no other process was using the target port.
   - Ensured Docker Compose mapped the correct ports (`4317`, `4318`, etc).

2. **Inspected Docker Compose and Collector Config**
   - Validated that the OTLP HTTP receiver was enabled in `otel-collector-config.yaml`:
     ```yaml
     receivers:
       otlp:
         protocols:
           grpc:
           http:
     ```
   - Confirmed correct port mappings in Compose files.

3. **Tested Collector Endpoints**
   - Attempted `curl http://localhost:4318/health` and `/health/status`.
   - Got `connection reset` or `404` (expected if health extension not enabled).
   - Verified with a minimal config and different ports (e.g., `8080`).
   - Used a temporary container with `curl` to test from within the Docker network.

4. **Analyzed Collector Logs**
   - Looked for lines indicating the OTLP HTTP server was running on the correct port.
   - Checked for errors, panics, or port binding issues.

5. **Tried Health Check Extension**
   - Added the `health_check` extension to expose `/health` on port 13133.
   - Mapped `13133:13133` in Compose and tested with `curl http://localhost:13133/health`.

6. **Ruled Out Host Issues**
   - Restarted Docker Desktop and the host machine.
   - Disabled firewall/antivirus to rule out port blocking.
   - Removed orphaned containers.

## What Actually Works for Testing

- **The Collector's built-in `/health` endpoint is only available if the `health_check` extension is enabled and port 13133 is mapped.**
- **The OTLP HTTP endpoint (`4318`) does NOT provide a health endpoint by default.**
- **A 404 from `/health` means the collector is running, but the endpoint is not implemented.**

## Recommended Testing Approach

1. **Use Your Own Health Check Logic**
   - Leverage `check_telemetry_health()` from `health_check.py` to verify the collector is up and accepting telemetry.
   - This can be called directly in a script or test, independent of FastAPI.

2. **Minimal Pytest Example:**
   ```python
   def test_otel_collector_health():
       from health_check import check_telemetry_health
       result = check_telemetry_health()
       assert result["status"] == "healthy"
   ```

3. **For CI/CD:**
   - Run a script that calls your health check and exits with status 0 if healthy.

4. **If you need a real HTTP health endpoint:**
   - Enable the `health_check` extension and map port 13133.
   - Otherwise, rely on your internal health check logic.

## Troubleshooting Checklist

- [ ] Collector config has `http:` under `otlp` receiver
- [ ] Correct ports mapped in Compose
- [ ] No host firewall or Docker Desktop issues
- [ ] Collector logs show HTTP server running
- [ ] Use internal health check for most reliable results

---

*Documented by Ty the Programmer – see code for latest best practices.*
