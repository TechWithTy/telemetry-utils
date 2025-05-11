# c:\Users\tyriq\Documents\Github\lead_ignite_backend_3.0\backend\app\core\telemetry\client.py
import logging
import os
from contextlib import contextmanager
from typing import Any

import grpc
from circuitbreaker import circuit
from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk._logs import (
    LoggerProvider,
    LoggingHandler,
)
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logger = logging.getLogger(__name__)


class TelemetryClient:
    def __init__(self, service_name: str, service_version: str = "1.0.0"):
        """Production-ready telemetry client with metrics and proper shutdown."""
        self.service_name = service_name
        self.service_version = service_version
        self._initialize_tracing()
        self._initialize_metrics()
        self._initialize_logging()

    @circuit(
        failure_threshold=3,
        recovery_timeout=30,
        expected_exception=(grpc.RpcError, ConnectionError, RuntimeError),
        fallback_function=lambda e: logger.warning(f"Telemetry circuit open: {str(e)}"),
    )
    def _initialize_tracing(self):
        """Initialize tracing with production-ready configuration."""
        resource = Resource.create(
            {
                "service.name": self.service_name,
                "service.version": self.service_version,
                "environment": os.getenv("ENVIRONMENT", "development"),
            }
        )

        trace.set_tracer_provider(TracerProvider(resource=resource))

        otlp_exporter = OTLPSpanExporter(
            endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
            insecure=os.getenv("OTEL_EXPORTER_OTLP_INSECURE", "false").lower()
            == "true",
        )

        span_processor = BatchSpanProcessor(otlp_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)

    @circuit(
        failure_threshold=3,
        recovery_timeout=30,
        expected_exception=(grpc.RpcError, ConnectionError, RuntimeError),
    )
    def _initialize_metrics(self):
        """Initialize metrics collection."""
        metric_exporter = OTLPMetricExporter(
            endpoint=os.getenv(
                "OTEL_EXPORTER_OTLP_METRICS_ENDPOINT", "http://localhost:4317"
            )
        )
        metric_reader = PeriodicExportingMetricReader(metric_exporter)
        metrics.set_meter_provider(MeterProvider(metric_readers=[metric_reader]))

    @circuit(
        failure_threshold=3,
        recovery_timeout=30,
        expected_exception=(grpc.RpcError, ConnectionError, RuntimeError),
    )
    def _initialize_logging(self):
        """Initialize logging with OTLP exporter for Loki"""
        resource = Resource.create(
            {
                "service.name": self.service_name,
                "service.version": self.service_version,
                "environment": os.getenv("ENVIRONMENT", "development"),
            }
        )
        logger_provider = LoggerProvider(resource=resource)
        log_exporter = OTLPLogExporter(
            endpoint=os.getenv(
                "OTEL_EXPORTER_OTLP_LOGS_ENDPOINT", "http://localhost:4317"
            ),
            insecure=os.getenv("OTEL_EXPORTER_OTLP_INSECURE", "false").lower() == "true",
        )
        log_processor = BatchLogRecordProcessor(log_exporter)
        logger_provider.add_log_record_processor(log_processor)
        set_logger_provider(logger_provider)
        # Pipe Python logs into OpenTelemetry
        handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
        logging.getLogger().addHandler(handler)

    def instrument_fastapi(self, app):
        """Instrument FastAPI application for automatic tracing."""
        FastAPIInstrumentor.instrument_app(app)

    @contextmanager
    def start_span(self, name: str, attributes: dict[str, Any] | None):
        """Context manager for creating spans with proper error handling."""
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span(name) as span:
            try:
                if attributes:
                    for k, v in attributes.items():
                        span.set_attribute(k, str(v))
                yield span
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR))
                logger.error(f"Error in span {name}: {str(e)}")
                raise

    def get_tracer(self):
        """Get the configured tracer instance."""
        return trace.get_tracer(__name__)

    def shutdown(self):
        """Properly shutdown telemetry providers."""
        trace.get_tracer_provider().shutdown()
        metrics.get_meter_provider().shutdown()

    def span_pulsar_operation(self, operation: str, attributes: dict[str, Any] | None):
        """
        Context manager for tracing a Pulsar client operation.
        Usage: with telemetry_client.span_pulsar_operation('send_message'):
        """
        return self.start_span(f"pulsar.{operation}", attributes)

    def span_cache_operation(self, operation: str, attributes: dict[str, Any] | None):
        """
        Context manager for tracing a VALKEY cache operation.
        Usage: with telemetry_client.span_cache_operation('get'):
        """
        return self.start_span(f"cache.{operation}", attributes)

    def span_celery_operation(self, operation: str, attributes: dict[str, Any] | None):
        """
        Context manager for tracing Celery operations.
        Usage: with telemetry_client.span_celery_operation('execute', {'task_name': name}):
        """
        return self.start_span(f"celery.{operation}", attributes)
