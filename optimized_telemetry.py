"""
Optimized telemetry configuration to fix service name issues and trace gaps.

This module provides fixes for:
1. "<root span not yet received>" service names
2. Large gaps in trace timelines
3. Slow request performance

Key improvements:
- Proper service name configuration
- Root span creation in middleware
- Comprehensive instrumentation
- Parallel operation tracing
"""

import os
import time
import uuid
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry import trace

from .client import TelemetryClient
from .decorators import measure_performance, trace_function, track_errors
from .health_check import health_response

# Initialize at module level for easy access
telemetry_client: Optional[TelemetryClient] = None


def setup_optimized_telemetry(app: FastAPI) -> TelemetryClient:
    """
    Optimized telemetry setup that fixes service name issues and trace gaps.
    
    Key fixes:
    1. Explicit service name configuration
    2. Instance ID for better trace correlation
    3. Root span middleware for proper hierarchy
    4. Comprehensive instrumentation order
    
    Args:
        app: FastAPI application instance

    Returns:
        Configured TelemetryClient instance
    """
    global telemetry_client

    # Get service configuration
    service_name = os.getenv("SERVICE_NAME", "fastapi-connect-backend")
    service_version = os.getenv("SERVICE_VERSION", "1.0.0")
    environment = os.getenv("ENVIRONMENT", "production")
    
    # Create unique instance ID for better tracing
    instance_id = f"{service_name}-{uuid.uuid4().hex[:8]}"
    
    print(f"[TELEMETRY] Initializing optimized telemetry for {service_name} (instance: {instance_id})")

    # Initialize OpenTelemetry client with explicit configuration
    telemetry_client = TelemetryClient(
        service_name=service_name,
        service_version=service_version,
        auto_init=False,  # We'll configure exporters manually
        instance_id=instance_id,
        environment=environment
    )

    # Configure OTLP exporter for Grafana Cloud Tempo
    if os.getenv("USE_MANAGED_SERVICES") == "true":
        print("[TELEMETRY] Configuring Grafana Cloud Tempo integration", flush=True)
        # Grafana Cloud configuration
        otlp_endpoint = os.getenv("TEMPO_EXPORTER_ENDPOINT")
        tempo_username = os.getenv("TEMPO_USERNAME")  
        tempo_api_key = os.getenv("TEMPO_API_KEY")
        
        print(f"[TELEMETRY] Service: {service_name}")
        print(f"[TELEMETRY] Instance: {instance_id}")
        print(f"[TELEMETRY] Environment: {environment}")
        print(f"[TELEMETRY] Endpoint: {otlp_endpoint}")
        print(f"[TELEMETRY] Username: {tempo_username}")
        print(f"[TELEMETRY] API Key: {'✓' if tempo_api_key else '✗'}")
        
        if not otlp_endpoint or not tempo_username or not tempo_api_key:
            print("[WARNING] Grafana Cloud credentials not properly configured", flush=True)
            print("  TEMPO_EXPORTER_ENDPOINT:", "✓" if otlp_endpoint else "✗")
            print("  TEMPO_USERNAME:", "✓" if tempo_username else "✗")
            print("  TEMPO_API_KEY:", "✓" if tempo_api_key else "✗")
        
        # Use basic authentication for Grafana Cloud Tempo (gRPC metadata format)
        import base64
        credentials = f"{tempo_username}:{tempo_api_key}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        # gRPC uses metadata, not headers - and expects key-value tuples
        headers = (
            ("authorization", f"Basic {encoded_credentials}"),
        )
        
        span_exporter = OTLPSpanExporter(
            endpoint=otlp_endpoint,
            headers=headers,
            timeout=30,
            insecure=False  # Use secure connection for Grafana Cloud
        )
        
        # Also configure metrics exporter for Grafana Cloud
        metrics_endpoint = otlp_endpoint.replace("/api/traces", "/api/push")
        print(f"[TELEMETRY] Metrics endpoint: {metrics_endpoint}", flush=True)
        metric_exporter = OTLPMetricExporter(
            endpoint=metrics_endpoint,
            headers=headers,
            timeout=30,
            insecure=False  # Use secure connection for Grafana Cloud
        )
        
        print("[TELEMETRY] Grafana Cloud exporters configured with Basic Auth", flush=True)
    else:
        print("[TELEMETRY] Using local Tempo setup", flush=True)
        # Local Tempo setup
        local_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        span_exporter = OTLPSpanExporter(endpoint=local_endpoint)
        metric_exporter = OTLPMetricExporter(endpoint=local_endpoint)
    
    # Configure telemetry client with the exporters BEFORE FastAPI instrumentation
    telemetry_client.configure_exporters(span_exporter, metric_exporter)
    
    # Add root span middleware BEFORE other middleware
    add_root_span_middleware(app)
    
    # Add comprehensive tracing middleware
    add_comprehensive_tracing_middleware(app)
    
    # Instrument FastAPI with OpenTelemetry AFTER middleware setup
    telemetry_client.instrument_fastapi(app)
    
    # Add Prometheus instrumentation if enabled (will use same prometheus_client)
    if os.getenv("ENABLE_PROMETHEUS", "true").lower() == "true":
        try:
            from prometheus_fastapi_instrumentator import Instrumentator
            
            # Create instrumentator with custom metrics
            instrumentator = Instrumentator(
                should_group_status_codes=True,
                should_ignore_untemplated=True
            )
            
            # Add default metrics
            instrumentator.instrument(app)
            
            # Keep existing prometheus-client metrics
            @app.on_event("startup")
            async def expose_metrics():
                instrumentator.expose(app)
        except ImportError:
            print("[WARNING] prometheus_fastapi_instrumentator not available", flush=True)
    
    print(f"[TELEMETRY] Optimized telemetry initialized successfully for {service_name}")
    return telemetry_client


def add_root_span_middleware(app: FastAPI):
    """
    Add middleware to create proper root spans for all requests.
    This fixes the '<root span not yet received>' issue.
    """
    @app.middleware("http")
    async def root_span_middleware(request: Request, call_next):
        """Create a root span for each request to ensure proper trace hierarchy."""
        tracer = trace.get_tracer(__name__)
        
        # Create root span with request information
        span_name = f"{request.method} {request.url.path}"
        
        with tracer.start_as_current_span(span_name) as span:
            # Set span attributes for better observability
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            span.set_attribute("http.scheme", request.url.scheme)
            span.set_attribute("http.host", request.url.hostname or "unknown")
            span.set_attribute("http.target", request.url.path)
            
            # Add query parameters if present
            if request.query_params:
                span.set_attribute("http.query", str(request.query_params))
            
            # Add user agent if available
            user_agent = request.headers.get("user-agent")
            if user_agent:
                span.set_attribute("http.user_agent", user_agent)
            
            # Add request ID for correlation
            request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
            span.set_attribute("request.id", request_id)
            
            start_time = time.time()
            
            try:
                # Process the request
                response = await call_next(request)
                
                # Set response attributes
                span.set_attribute("http.status_code", response.status_code)
                span.set_attribute("http.response.size", 
                                 response.headers.get("content-length", "unknown"))
                
                # Set span status based on HTTP status
                if response.status_code >= 400:
                    span.set_status(trace.Status(trace.StatusCode.ERROR))
                else:
                    span.set_status(trace.Status(trace.StatusCode.OK))
                
                return response
                
            except Exception as e:
                # Record exception in span
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise
            
            finally:
                # Record request duration
                duration = time.time() - start_time
                span.set_attribute("http.duration_ms", duration * 1000)


def add_comprehensive_tracing_middleware(app: FastAPI):
    """
    Add middleware for comprehensive request tracing to eliminate gaps.
    """
    @app.middleware("http")
    async def comprehensive_tracing_middleware(request: Request, call_next):
        """Add detailed tracing for request processing stages."""
        tracer = trace.get_tracer(__name__)
        
        # Get current span (should be the root span from previous middleware)
        root_span = trace.get_current_span()
        
        with tracer.start_as_current_span("request_processing") as processing_span:
            processing_span.set_attribute("stage", "middleware")
            
            # Trace request parsing
            with tracer.start_as_current_span("request_parsing") as parse_span:
                parse_start = time.time()
                
                # Parse request details
                content_type = request.headers.get("content-type", "unknown")
                content_length = request.headers.get("content-length", "0")
                
                parse_span.set_attribute("http.content_type", content_type)
                parse_span.set_attribute("http.content_length", content_length)
                
                # Check if this is a JSON request
                if "application/json" in content_type:
                    parse_span.set_attribute("request.format", "json")
                
                parse_duration = time.time() - parse_start
                parse_span.set_attribute("parsing.duration_ms", parse_duration * 1000)
            
            # Process the request with timing
            process_start = time.time()
            
            try:
                response = await call_next(request)
                
                process_duration = time.time() - process_start
                processing_span.set_attribute("processing.duration_ms", process_duration * 1000)
                processing_span.set_attribute("processing.status", "success")
                
                return response
                
            except Exception as e:
                process_duration = time.time() - process_start
                processing_span.set_attribute("processing.duration_ms", process_duration * 1000)
                processing_span.set_attribute("processing.status", "error")
                processing_span.set_attribute("error.type", type(e).__name__)
                processing_span.set_attribute("error.message", str(e))
                raise


@asynccontextmanager
async def traced_operation(operation_name: str, **attributes):
    """
    Context manager for tracing individual operations with proper error handling.
    Use this to wrap database calls, external API calls, etc.
    """
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span(operation_name) as span:
        # Set provided attributes
        for key, value in attributes.items():
            span.set_attribute(key, str(value))
        
        start_time = time.time()
        
        try:
            yield span
            
            # Mark as successful
            duration = time.time() - start_time
            span.set_attribute("operation.duration_ms", duration * 1000)
            span.set_attribute("operation.status", "success")
            span.set_status(trace.Status(trace.StatusCode.OK))
            
        except Exception as e:
            # Record the error
            duration = time.time() - start_time
            span.set_attribute("operation.duration_ms", duration * 1000)
            span.set_attribute("operation.status", "error")
            span.set_attribute("error.type", type(e).__name__)
            span.set_attribute("error.message", str(e))
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            raise


async def trace_async_operations(*operations, operation_name: str = "parallel_operations"):
    """
    Trace multiple async operations running in parallel.
    This helps eliminate gaps in traces when operations run concurrently.
    
    Args:
        *operations: Async functions or coroutines to run in parallel
        operation_name: Name for the parent span
    
    Returns:
        Results from all operations
    """
    import asyncio
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span(operation_name) as parent_span:
        parent_span.set_attribute("operations.count", len(operations))
        
        start_time = time.time()
        
        try:
            # Run all operations in parallel
            results = await asyncio.gather(*operations, return_exceptions=True)
            
            duration = time.time() - start_time
            parent_span.set_attribute("operations.duration_ms", duration * 1000)
            
            # Check for exceptions
            exceptions = [r for r in results if isinstance(r, Exception)]
            if exceptions:
                parent_span.set_attribute("operations.errors", len(exceptions))
                parent_span.set_attribute("operations.status", "partial_failure")
                # Record first exception
                parent_span.record_exception(exceptions[0])
            else:
                parent_span.set_attribute("operations.status", "success")
            
            return results
            
        except Exception as e:
            duration = time.time() - start_time
            parent_span.set_attribute("operations.duration_ms", duration * 1000)
            parent_span.set_attribute("operations.status", "failure")
            parent_span.record_exception(e)
            raise


def get_telemetry() -> TelemetryClient:
    """
    Get the configured telemetry client instance.

    Raises:
        RuntimeError: If telemetry hasn't been initialized
    """
    if telemetry_client is None:
        raise RuntimeError("Telemetry not initialized. Call setup_optimized_telemetry() first.")
    return telemetry_client


# Export the optimized setup function as the main setup function
setup_telemetry = setup_optimized_telemetry

# Export utility functions
__all__ = [
    'setup_optimized_telemetry',
    'setup_telemetry',  # Alias for compatibility
    'get_telemetry',
    'traced_operation',
    'trace_async_operations',
    'add_root_span_middleware',
    'add_comprehensive_tracing_middleware'
]
