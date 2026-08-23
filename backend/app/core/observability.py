import logging
import time
from collections.abc import Awaitable, Callable

import structlog
from fastapi import Request, Response
from opentelemetry import propagate, trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased
from opentelemetry.trace import SpanKind, Status, StatusCode
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

from app.core.config import Settings


HTTP_REQUESTS = Counter(
    'stock_ai_http_requests_total',
    'Total HTTP requests processed by the backend.',
    ('method', 'route', 'status_code'),
)
HTTP_REQUEST_DURATION = Histogram(
    'stock_ai_http_request_duration_seconds',
    'Backend HTTP request duration in seconds.',
    ('method', 'route'),
)
HTTP_REQUESTS_IN_PROGRESS = Gauge(
    'stock_ai_http_requests_in_progress',
    'Backend HTTP requests currently being processed.',
    ('method',),
)


def configure_observability(settings: Settings) -> None:
    configure_logging(settings.log_level)
    if settings.tracing_enabled:
        configure_tracing(settings)


def configure_logging(log_level: str) -> None:
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(level=level, format='%(message)s')
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt='iso', utc=True),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        cache_logger_on_first_use=True,
    )


def configure_tracing(settings: Settings) -> None:
    if not settings.otel_exporter_otlp_endpoint:
        raise ValueError('OTEL_EXPORTER_OTLP_ENDPOINT is required when tracing is enabled')
    if not 0 <= settings.otel_sample_ratio <= 1:
        raise ValueError('OTEL_SAMPLE_RATIO must be between 0 and 1')

    provider = TracerProvider(
        resource=Resource.create(
            {
                'service.name': settings.otel_service_name,
                'deployment.environment.name': settings.app_env,
            }
        ),
        sampler=ParentBased(TraceIdRatioBased(settings.otel_sample_ratio)),
    )
    provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(
                endpoint=settings.otel_exporter_otlp_endpoint,
                timeout=5,
            )
        )
    )
    trace.set_tracer_provider(provider)


def metrics_response() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


async def observe_request(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
    *,
    metrics_enabled: bool,
    route_prefix: str = '',
) -> Response:
    method = request.method
    started_at = time.perf_counter()
    status_code = 500
    tracer = trace.get_tracer('stock-ai.http')
    parent_context = propagate.extract(request.headers)

    if metrics_enabled:
        HTTP_REQUESTS_IN_PROGRESS.labels(method=method).inc()

    with tracer.start_as_current_span(
        f'{method} {request.url.path}',
        context=parent_context,
        kind=SpanKind.SERVER,
    ) as span:
        span_context = span.get_span_context()
        trace_id = f'{span_context.trace_id:032x}' if span_context.is_valid else None
        span_id = f'{span_context.span_id:016x}' if span_context.is_valid else None
        span.set_attribute('http.request.method', method)
        span.set_attribute('url.path', request.url.path)
        try:
            response = await call_next(request)
            status_code = response.status_code
            span.set_attribute('http.response.status_code', status_code)
            if status_code >= 500:
                span.set_status(Status(StatusCode.ERROR))
            if trace_id:
                response.headers['x-trace-id'] = trace_id
            return response
        except Exception as exc:
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            raise
        finally:
            route = getattr(request.scope.get('route'), 'path', request.url.path)
            if route_prefix and request.url.path.startswith(route_prefix) and not route.startswith(route_prefix):
                route = f'{route_prefix}{route}'
            duration = time.perf_counter() - started_at
            if metrics_enabled:
                HTTP_REQUESTS.labels(method=method, route=route, status_code=str(status_code)).inc()
                HTTP_REQUEST_DURATION.labels(method=method, route=route).observe(duration)
                HTTP_REQUESTS_IN_PROGRESS.labels(method=method).dec()
            structlog.get_logger('http').info(
                'request_completed',
                method=method,
                route=route,
                status_code=status_code,
                duration_ms=round(duration * 1000, 2),
                request_id=getattr(request.state, 'request_id', None),
                trace_id=trace_id,
                span_id=span_id,
            )
