
OpenTelemetry FastAPI Instrumentation

pypi

This library provides automatic and manual instrumentation of FastAPI web frameworks, instrumenting http requests served by applications utilizing the framework.

auto-instrumentation using the opentelemetry-instrumentation package is also supported.
Installation

pip install opentelemetry-instrumentation-fastapi

References

    OpenTelemetry Project

    OpenTelemetry Python Examples

API
Usage

import fastapi
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

app = fastapi.FastAPI()

@app.get("/foobar")
async def foobar():
    return {"message": "hello world"}

FastAPIInstrumentor.instrument_app(app)

Configuration
Exclude lists

To exclude certain URLs from tracking, set the environment variable OTEL_PYTHON_FASTAPI_EXCLUDED_URLS (or OTEL_PYTHON_EXCLUDED_URLS to cover all instrumentations) to a string of comma delimited regexes that match the URLs.

For example,

export OTEL_PYTHON_FASTAPI_EXCLUDED_URLS="client/.*/info,healthcheck"

will exclude requests such as https://site/client/123/info and https://site/xyz/healthcheck.

You can also pass comma delimited regexes directly to the instrument_app method:

FastAPIInstrumentor.instrument_app(app, excluded_urls="client/.*/info,healthcheck")

Request/Response hooks

This instrumentation supports request and response hooks. These are functions that get called right after a span is created for a request and right before the span is finished for the response.

    The server request hook is passed a server span and ASGI scope object for every incoming request.

    The client request hook is called with the internal span, and ASGI scope and event when the method receive is called.

    The client response hook is called with the internal span, and ASGI scope and event when the method send is called.

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.trace import Span
from typing import Any

def server_request_hook(span: Span, scope: dict[str, Any]):
    if span and span.is_recording():
        span.set_attribute("custom_user_attribute_from_request_hook", "some-value")

def client_request_hook(span: Span, scope: dict[str, Any], message: dict[str, Any]):
    if span and span.is_recording():
        span.set_attribute("custom_user_attribute_from_client_request_hook", "some-value")

def client_response_hook(span: Span, scope: dict[str, Any], message: dict[str, Any]):
    if span and span.is_recording():
        span.set_attribute("custom_user_attribute_from_response_hook", "some-value")

FastAPIInstrumentor().instrument(server_request_hook=server_request_hook, client_request_hook=client_request_hook, client_response_hook=client_response_hook)

Capture HTTP request and response headers

You can configure the agent to capture specified HTTP headers as span attributes, according to the semantic convention.
Request headers

To capture HTTP request headers as span attributes, set the environment variable OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_REQUEST to a comma delimited list of HTTP header names, or pass the http_capture_headers_server_request keyword argument to the instrument_app method.

For example using the environment variable,

export OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_REQUEST="content-type,custom_request_header"

will extract content-type and custom_request_header from the request headers and add them as span attributes.

Request header names in FastAPI are case-insensitive. So, giving the header name as CUStom-Header in the environment variable will capture the header named custom-header.

Regular expressions may also be used to match multiple headers that correspond to the given pattern. For example:

export OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_REQUEST="Accept.*,X-.*"

Would match all request headers that start with Accept and X-.

To capture all request headers, set OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_REQUEST to ".*".

export OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_REQUEST=".*"

The name of the added span attribute will follow the format http.request.header.<header_name> where <header_name> is the normalized HTTP header name (lowercase, with - replaced by _). The value of the attribute will be a single item list containing all the header values.

For example: http.request.header.custom_request_header = ["<value1>", "<value2>"]
Response headers

To capture HTTP response headers as span attributes, set the environment variable OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_RESPONSE to a comma delimited list of HTTP header names, or pass the http_capture_headers_server_response keyword argument to the instrument_app method.

For example using the environment variable,

export OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_RESPONSE="content-type,custom_response_header"

will extract content-type and custom_response_header from the response headers and add them as span attributes.

Response header names in FastAPI are case-insensitive. So, giving the header name as CUStom-Header in the environment variable will capture the header named custom-header.

Regular expressions may also be used to match multiple headers that correspond to the given pattern. For example:

export OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_RESPONSE="Content.*,X-.*"

Would match all response headers that start with Content and X-.

To capture all response headers, set OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_RESPONSE to ".*".

export OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_RESPONSE=".*"

The name of the added span attribute will follow the format http.response.header.<header_name> where <header_name> is the normalized HTTP header name (lowercase, with - replaced by _). The value of the attribute will be a list containing the header values.

For example: http.response.header.custom_response_header = ["<value1>", "<value2>"]
Sanitizing headers

In order to prevent storing sensitive data such as personally identifiable information (PII), session keys, passwords, etc, set the environment variable OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SANITIZE_FIELDS to a comma delimited list of HTTP header names to be sanitized, or pass the http_capture_headers_sanitize_fields keyword argument to the instrument_app method.

Regexes may be used, and all header names will be matched in a case-insensitive manner.

For example using the environment variable,

export OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SANITIZE_FIELDS=".*session.*,set-cookie"

will replace the value of headers such as session-id and set-cookie with [REDACTED] in the span.

Note

The environment variable names used to capture HTTP headers are still experimental, and thus are subject to change.
API

class opentelemetry.instrumentation.fastapi.FastAPIInstrumentor(*args, **kwargs)[source]

    Bases: BaseInstrumentor

    An instrumentor for FastAPI

    See BaseInstrumentor

    static instrument_app(app, server_request_hook=None, client_request_hook=None, client_response_hook=None, tracer_provider=None, meter_provider=None, excluded_urls=None, http_capture_headers_server_request=None, http_capture_headers_server_response=None, http_capture_headers_sanitize_fields=None, exclude_spans=None)[source]

        Instrument an uninstrumented FastAPI application.

        Parameters:

                app – The fastapi ASGI application callable to forward requests to.

                server_request_hook (Optional[Callable[[Span, Dict[str, Any]], None]]) – Optional callback which is called with the server span and ASGI scope object for every incoming request.

                client_request_hook (Optional[Callable[[Span, Dict[str, Any], Dict[str, Any]], None]]) – Optional callback which is called with the internal span, and ASGI scope and event which are sent as dictionaries for when the method receive is called.

                client_response_hook (Optional[Callable[[Span, Dict[str, Any], Dict[str, Any]], None]]) – Optional callback which is called with the internal span, and ASGI scope and event which are sent as dictionaries for when the method send is called.

                tracer_provider – The optional tracer provider to use. If omitted the current globally configured one is used.

                meter_provider – The optional meter provider to use. If omitted the current globally configured one is used.

                excluded_urls – Optional comma delimited string of regexes to match URLs that should not be traced.

                http_capture_headers_server_request (Optional[list[str]]) – Optional list of HTTP headers to capture from the request.

                http_capture_headers_server_response (Optional[list[str]]) – Optional list of HTTP headers to capture from the response.

                http_capture_headers_sanitize_fields (Optional[list[str]]) – Optional list of HTTP headers to sanitize.

                exclude_spans (Optional[list[Literal['receive', 'send']]]) – Optionally exclude HTTP send and/or receive spans from the trace.

    static uninstrument_app(app)[source]

    instrumentation_dependencies()[source]

        Return a list of python packages with versions that the will be instrumented.

        The format should be the same as used in requirements.txt or pyproject.toml.

        For example, if an instrumentation instruments requests 1.x, this method should look like: :rtype: Collection[str]

            def instrumentation_dependencies(self) -> Collection[str]:

                return [‘requests ~= 1.0’]

        This will ensure that the instrumentation will only be used when the specified library is present in the environment.

