Best practices for OpenTelemetry traces

There are various guidelines to keep in mind when working with OpenTelemetry, as with almost any other area of software engineering.

For OpenTelemetry Traces, we recommend following these best practices.
Put stack traces and errors on events
An event

is a human-readable message on a span that represents “something happening” during its lifetime. An event is, therefore, better suited to display information about errors.
Make use of attributes

An attribute you do not use cannot be detected in Dynatrace and cannot give you any further insights into your system.

    Use well-annotated spans (use attributes that are recognizable, readable, and understandable).
    Set attributes that provide detailed information, such as URLs, methods, user data (location, device type, OS (Operation Systems), software data (version, feature flags), infrastructure-related attributes, and many more (see semantic conventions﻿

    ).
    It might be worth creating a shared library of attributes to catalog important data.

Implement context propagation

Context propagation connects the individual traces over all tiers of your application. If you have no context propagation, your spans will be orphaned and create multiple traces instead of all spans created as child spans within one trace.
Allocate span kind according to the span's use

    Server and Consumer spans are used for receiving data from other processes (for sync and async respectively)
    Internal spans are used for intermediate operations
    Client and Producer spans are used for spans sending data to outer processes (sync and async respectively)

Use automatic instrumentation for easy setup

Simplicity of use has two advantages:

    It reduces the potential for human error
    It decreases labor time and costs

Use OneAgent for easier transfer to Dynatrace

OneAgent brings many benefits, including automatic trace ingestion in some languages. See OpenTelemetry traces with OneAgent.
Name your tracer, spans, and attributes

It will help your observability, especially in case of an error, as the root cause will be easier to track down.

In manual instrumentation, you must set an individual name for each span you create.
End your spans

Whenever you start a span, you need to end it. Otherwise, no data will be sent.
Initialize OpenTelemetry first

Initialize OpenTelemetry before using any library that you want to instrument. Otherwise, no spans will be created, and your calls will be missing.
Use an exporter

Whether or not you use the Collector, an exporter is required to send your data to the desired backend.
Set attributes at span start
Samplers can only consider information already present during span creation

.
Make root or parent spans active
Languages with implicit context propagation do not set newly created spans﻿ as the active span in the current context by default; this might result in split traces.
