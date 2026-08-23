# Observability

The backend emits structured JSON request logs, Prometheus metrics, request correlation IDs, and optional OpenTelemetry traces.

## Metrics

Prometheus metrics are available at `GET /metrics`. The Kubernetes backend pod annotations enable discovery by Prometheus installations that honor standard scrape annotations. The endpoint is intentionally not exposed through the application ingress, whose backend route is limited to `/api`.

Application metrics include:

- `stock_ai_http_requests_total` by method, templated route, and status code
- `stock_ai_http_request_duration_seconds` by method and templated route
- `stock_ai_http_requests_in_progress` by method
- Default Python process and runtime metrics from `prometheus-client`

Set `METRICS_ENABLED=false` to stop collecting HTTP request metrics. Platform operators should restrict direct access to the backend service and `/metrics` with cluster network policy or equivalent controls.

## Logs

Request completion events are JSON objects containing method, templated route, status code, duration, request ID, and trace/span IDs when tracing is active. Clients may supply `X-Request-Id`; otherwise the backend creates one and returns it in the response.

Set `LOG_LEVEL` to `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`. Production should normally use `INFO` and send container standard output to the platform log collector.

## Traces

Tracing is disabled by default. To export OTLP traces over HTTP:

```bash
TRACING_ENABLED=true
OTEL_SERVICE_NAME=stock-ai-backend
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector.observability:4318/v1/traces
OTEL_SAMPLE_RATIO=0.1
```

The sample ratio must be between `0` and `1`. Parent trace context is extracted from incoming requests, and sampled responses include `X-Trace-Id` for support correlation. Use a collector endpoint reachable from the backend workload and protect it from public traffic.

## Initial Production Signals

Alert on sustained server errors, elevated p95 request latency, unavailable ready replicas, repeated container restarts, and failed migration jobs. Thresholds should be calibrated in staging before paging is enabled.
