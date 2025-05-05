OpenTelemetry Python

Slack Build Status 0 Build Status 1 Minimum Python Version Release Read the Docs
Project Status

See the OpenTelemetry Instrumentation for Python.
Signal 	Status 	Project
Traces 	Stable 	N/A
Metrics 	Stable 	N/A
Logs 	Experimental 	N/A

Project versioning information and stability guarantees can be found here.
Getting started

You can find the getting started guide for OpenTelemetry Python here.

If you are looking for examples on how to use the OpenTelemetry API to instrument your code manually, or how to set up the OpenTelemetry Python SDK, see https://opentelemetry.io/docs/instrumentation/python/manual/.
Python Version Support

This project ensures compatibility with the current supported versions of the Python. As new Python versions are released, support for them is added and as old Python versions reach their end of life, support for them is removed.

We add support for new Python versions no later than 3 months after they become stable.

We remove support for old Python versions 6 months after they reach their end of life.
Documentation

The online documentation is available at https://opentelemetry-python.readthedocs.io/. To access the latest version of the documentation, see https://opentelemetry-python.readthedocs.io/en/latest/.
Install

This repository includes multiple installable packages. The opentelemetry-api package includes abstract classes and no-op implementations that comprise the OpenTelemetry API following the OpenTelemetry specification. The opentelemetry-sdk package is the reference implementation of the API.

Libraries that produce telemetry data should only depend on opentelemetry-api, and defer the choice of the SDK to the application developer. Applications may depend on opentelemetry-sdk or another package that implements the API.

The API and SDK packages are available on the Python Package Index (PyPI). You can install them via pip with the following commands:

pip install opentelemetry-api
pip install opentelemetry-sdk

The exporter/ directory includes OpenTelemetry exporter packages. You can install the packages separately with the following command:

pip install opentelemetry-exporter-{exporter}

The propagator/ directory includes OpenTelemetry propagator packages. You can install the packages separately with the following command:

pip install opentelemetry-propagator-{propagator}

To install the development versions of these packages instead, clone or fork this repository and perform an editable install:

pip install -e ./opentelemetry-api -e ./opentelemetry-sdk -e ./opentelemetry-semantic-conventions

For additional exporter and instrumentation packages, see the opentelemetry-python-contrib repository.
Contributing

For information about contributing to OpenTelemetry Python, see CONTRIBUTING.md.

We meet weekly on Thursdays at 9AM PST. The meeting is subject to change depending on contributors' availability. Check the OpenTelemetry community calendar for specific dates and Zoom meeting links.

Meeting notes are available as a public Google doc.

Approvers (@open-telemetry/python-approvers):

    Emídio Neto, PicPay
    Jeremy Voss, Microsoft
    Owais Lone, Splunk
    Pablo Collins, Splunk
    Shalev Roda, Cisco
    Srikanth Chekuri, signoz.io
    Tammy Baylis, SolarWinds

Emeritus Approvers

    Ashutosh Goel, Cisco
    Carlos Alberto Cortez, Lightstep
    Christian Neumüller, Dynatrace
    Héctor Hernández, Microsoft
    Mauricio Vásquez, Kinvolk
    Nathaniel Ruiz Nowell, AWS
    Nikolay Sokolik, Oxeye
    Sanket Mehta, Cisco
    Tahir H. Butt, DataDog

For more information about the approver role, see the community repository.

Maintainers (@open-telemetry/python-maintainers):

    Aaron Abbott, Google
    Diego Hurtado, Lightstep
    Leighton Chen, Microsoft
    Riccardo Magliocchetti, Elastic

Emeritus Maintainers:

    Alex Boten, Lightstep
    Chris Kleinknecht, Google
    Owais Lone, Splunk
    Reiley Yang, Microsoft
    Srikanth Chekuri, signoz.io
    Yusuke Tsutsumi, Google

For more information about the maintainer role, see the community repository.