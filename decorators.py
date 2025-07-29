import logging
from functools import wraps
import inspect
from time import perf_counter
from typing import Any, Callable, TypeVar, cast, get_type_hints, ForwardRef, _AnnotatedAlias

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

# Helper to properly handle FastAPI dependency injection
def preserve_fastapi_signature(wrapper_fn, original_fn):
    """
    Preserves the function signature for FastAPI dependency injection.
    FastAPI analyzes the function signature to determine what dependencies to inject.
    """
    # Copy signature and annotations for FastAPI
    sig = inspect.signature(original_fn)
    wrapper_fn.__signature__ = sig
    wrapper_fn.__annotations__ = getattr(original_fn, '__annotations__', {})
    
    # Ensure we always preserve the original function for proper introspection
    # This is critical for FastAPI's signature analysis
    wrapper_fn.__wrapped__ = getattr(original_fn, '__wrapped__', original_fn)
    
    # Handle special FastAPI and Pydantic types
    for param_name, param in sig.parameters.items():
        # Preserve any pydantic Field information
        if hasattr(param, "default") and hasattr(param.default, "__pydantic_field__"):
            setattr(wrapper_fn, f"__pydantic_field_{param_name}__", param.default)
            
        # Special handling for path parameters
        if param_name in wrapper_fn.__annotations__:
            annotation = wrapper_fn.__annotations__[param_name]
            # Handle Annotated types specifically - crucial for path parameters
            if hasattr(annotation, "__origin__") and annotation.__origin__ is _AnnotatedAlias:
                setattr(wrapper_fn, f"__path_param_{param_name}__", True)
    
    # Copy docstring
    wrapper_fn.__doc__ = original_fn.__doc__
    
    # Copy FastAPI-specific attributes
    for attr in ["openapi_extra", "response_model", "responses", "status_code",
                "dependencies", "summary", "description", "response_description",
                "include_in_schema", "deprecated", "tags", "openapi_extra"]:
        if hasattr(original_fn, attr):
            setattr(wrapper_fn, attr, getattr(original_fn, attr))
    
    # Copy any type annotations that might be useful for Pydantic/FastAPI
    try:
        type_hints = get_type_hints(original_fn, include_extras=True)
        if type_hints:
            for name, hint in type_hints.items():
                if name not in wrapper_fn.__annotations__:
                    wrapper_fn.__annotations__[name] = hint
    except Exception as e:
        # If we can't get type hints with extras, try without
        logger.warning(f"Error getting type hints with extras: {e}")
        try:
            type_hints = get_type_hints(original_fn)
            if type_hints:
                for name, hint in type_hints.items():
                    if name not in wrapper_fn.__annotations__:
                        wrapper_fn.__annotations__[name] = hint
        except Exception as e2:
            logger.warning(f"Error getting type hints: {e2}")
                
    return wrapper_fn


def trace_function(
    name: str | None = None,
    attributes: dict[str, Any] | None = None,
    record_metrics: bool = True,
    capture_exceptions: bool = True,
) -> Callable[[T], T]:
    """
    Decorator that adds OpenTelemetry tracing to a function.
    This decorator is specifically designed to work with FastAPI routes.
    """
    def decorator(func: T) -> T:
        # Get function signature and type hints
        func_signature = inspect.signature(func)
        is_async = inspect.iscoroutinefunction(func)
        
        if is_async:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                span_name = name or f"{func.__module__}.{func.__name__}"
                tracer = trace.get_tracer(__name__)
                start_time = perf_counter()
                status = "success"

                with tracer.start_as_current_span(span_name) as span:
                    try:
                        if attributes:
                            for k, v in attributes.items():
                                span.set_attribute(k, str(v))

                        result = await func(*args, **kwargs)
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
            
            # Properly preserve the function signature for FastAPI
            wrapped = preserve_fastapi_signature(async_wrapper, func)
            # Also handle path parameters for routes like /{id}
            return cast(T, preserve_path_parameters(wrapped))
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
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
            
            # Properly preserve the function signature for FastAPI
            wrapped = preserve_fastapi_signature(sync_wrapper, func)
            # Also handle path parameters for routes like /{id}
            return cast(T, preserve_path_parameters(wrapped))

    return decorator


def track_errors(func: T) -> T:
    """
    Decorator to automatically record exceptions with full context (supports sync and async).
    This decorator is specifically designed to work with FastAPI routes.
    """
    is_async = inspect.iscoroutinefunction(func)
    
    if is_async:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                current_span = trace.get_current_span()
                if current_span.is_recording():
                    current_span.record_exception(e)
                    current_span.set_status(trace.Status(trace.StatusCode.ERROR))
                logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
                raise
                
        # Properly preserve the function signature for FastAPI
        wrapped = preserve_fastapi_signature(async_wrapper, func)
        # Also handle path parameters for routes like /{id}
        return cast(T, preserve_path_parameters(wrapped))
    else:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                current_span = trace.get_current_span()
                if current_span.is_recording():
                    current_span.record_exception(e)
                    current_span.set_status(trace.Status(trace.StatusCode.ERROR))
                logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
                raise
                
        # Properly preserve the function signature for FastAPI
        wrapped = preserve_fastapi_signature(sync_wrapper, func)
        # Also handle path parameters for routes like /{id}
        return cast(T, preserve_path_parameters(wrapped))


def measure_performance(threshold_ms: float = 100.0, level: str = "warn", record_metric: bool = True) -> Callable[[T], T]:
    """
    Decorator to measure the performance of a function and log warnings for slow operations.
    This decorator is specifically designed to work with FastAPI routes.
    """
    def decorator(func: T) -> T:
        is_async = inspect.iscoroutinefunction(func)
        
        if is_async:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = perf_counter()
                try:
                    return await func(*args, **kwargs)
                finally:
                    duration = (perf_counter() - start_time) * 1000
                    if duration > threshold_ms:
                        msg = f"Slow performance in {func.__name__}: {duration:.2f}ms"
                        logger.log(
                            logging.ERROR if level == "error" else logging.WARNING, msg
                        )
                        current_span = trace.get_current_span()
                        if current_span.is_recording():
                            current_span.set_attributes({
                                "func.slow_call": True,
                                "func.duration_ms": duration,
                                "func.threshold_ms": threshold_ms,
                            })
                        if record_metric:
                            REQUEST_LATENCY.record(duration, {"function": func.__name__, "slow": True})
            
            # Properly preserve the function signature for FastAPI
            wrapped = preserve_fastapi_signature(async_wrapper, func)
            # Also handle path parameters for routes like /{id}
            return cast(T, preserve_path_parameters(wrapped))
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
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
                            current_span.set_attributes({
                                "func.slow_call": True,
                                "func.duration_ms": duration,
                                "func.threshold_ms": threshold_ms,
                            })
                        if record_metric:
                            REQUEST_LATENCY.record(duration, {"function": func.__name__, "slow": True})
            
            # Properly preserve the function signature for FastAPI
            wrapped = preserve_fastapi_signature(sync_wrapper, func)
            # Also handle path parameters for routes like /{id}
            return cast(T, preserve_path_parameters(wrapped))

    return decorator


def preserve_path_parameters(func: Callable) -> Callable:
    """
    Special handler for FastAPI path parameters.
    This ensures UUID path parameters are correctly recognized by FastAPI.
    
    This should be used in addition to preserve_fastapi_signature for route handlers
    that have path parameters like {id} where id is a uuid.UUID type.
    """
    if hasattr(func, "__wrapped__"):
        original = func.__wrapped__
        # Copy path parameter annotations explicitly
        for param_name, param_type in getattr(original, "__annotations__", {}).items():
            if param_name in ["id"]:  # Common path parameters
                func.__annotations__[param_name] = param_type
                
        # Ensure we rebuild the signature with the correct path parameters
        sig = inspect.signature(original)
        func.__signature__ = sig
        
    return func
