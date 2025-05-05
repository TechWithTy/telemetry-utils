# Use official OpenTelemetry Collector image as base
FROM otel/opentelemetry-collector-contrib:latest

# Set working directory
WORKDIR /otel

# Copy OpenTelemetry Collector config if present
COPY ./otel-collector-config.yaml ./otel-collector-config.yaml

# Expose default OpenTelemetry ports
ENV OTEL_COLLECTOR_GRPC_PORT=${OTEL_COLLECTOR_GRPC_PORT:-4317}
ENV OTEL_COLLECTOR_HTTP_PORT=${OTEL_COLLECTOR_HTTP_PORT:-4318}
EXPOSE $OTEL_COLLECTOR_GRPC_PORT $OTEL_COLLECTOR_HTTP_PORT

# Default entrypoint and config (can be overridden in docker-compose)
CMD ["--config", "otel-collector-config.yaml"]

# Notes:
# - Place your otel-collector-config.yaml in the same directory or mount as a volume
# - Ports and config file can be overridden via env or compose