import logging
from functools import wraps
from time import perf_counter
from typing import Any, Callable, Dict, Optional, TypeVar

from opentelemetry import metrics, trace

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=Callable[..., Any])

# Global metrics for production monitoring
REQUEST_COUNT = metrics.get_meter(__name__).create_counter(
    "app.request.count", unit="1", description="Total request count"
)
REQUEST_LATENCY = metrics.get_meter(__name__).create_histogram(
    "app.request.latency.ms", unit="ms", description="Request latency distribution"
)
ERROR_COUNT = metrics.get_meter(__name__).create_counter(
    "app.error.count", unit="1", description="Total error count"
)


def trace_function(
    name: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
    record_metrics: bool = True,
    capture_exceptions: bool = True,
) -> Callable[[T], T]:
    """Production-ready tracing decorator with enhanced observability."""

    def decorator(func: T) -> T:
        @wraps(func)
        def wrapper(*args, **kwargs):
            span_name = name or f"{func.__module__}.{func.__name__}"
            tracer = trace.get_tracer(__name__)
            start_time = perf_counter()
            status = "success"

            with tracer.start_as_current_span(span_name) as span:
                try:
                    if attributes:
                        for k, v in attributes.items():
                            span.set_attribute(k, str(v))

                    result = func(*args, **kwargs)
                    return result

                except Exception as e:
                    status = "error"
                    if capture_exceptions:
                        span.record_exception(e)
                        span.set_status(trace.Status(trace.StatusCode.ERROR))
                        ERROR_COUNT.add(1, {"function": span_name})
                    logger.error(f"Error in {span_name}: {str(e)}", exc_info=True)
                    raise

                finally:
                    if record_metrics:
                        duration = (perf_counter() - start_time) * 1000
                        REQUEST_COUNT.add(1, {"function": span_name, "status": status})
                        REQUEST_LATENCY.record(duration, {"function": span_name})
                        if span.is_recording():
                            span.set_attribute("func.duration_ms", duration)
                            span.set_attribute("func.status", status)

        return wrapper

    return decorator


def track_errors(func: T) -> T:
    """Decorator to automatically record exceptions with full context."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            current_span = trace.get_current_span()
            if current_span.is_recording():
                current_span.record_exception(e)
                current_span.set_status(trace.Status(trace.StatusCode.ERROR))
            ERROR_COUNT.add(1, {"function": func.__name__})
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            raise

    return wrapper


def measure_performance(
    threshold_ms: float = 100.0, level: str = "warn", record_metric: bool = True
) -> Callable[[T], T]:
    """Decorator to measure and log slow function executions."""

    def decorator(func: T) -> T:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                duration = (perf_counter() - start_time) * 1000
                if duration > threshold_ms:
                    msg = f"Slow performance in {func.__name__}: {duration:.2f}ms"
                    logger.log(
                        logging.ERROR if level == "error" else logging.WARNING, msg
                    )

                    current_span = trace.get_current_span()
                    if current_span.is_recording():
                        current_span.set_attributes(
                            {
                                "func.slow_call": True,
                                "func.duration_ms": duration,
                                "func.threshold_ms": threshold_ms,
                            }
                        )

                    if record_metric:
                        REQUEST_LATENCY.record(
                            duration, {"function": func.__name__, "slow": True}
                        )

        return wrapper

    return decorator
