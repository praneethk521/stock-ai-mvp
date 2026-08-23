import pytest

from app.core.config import Settings
from app.core.observability import configure_tracing


def test_tracing_requires_an_otlp_endpoint():
    settings = Settings(tracing_enabled=True, otel_exporter_otlp_endpoint=None)

    with pytest.raises(ValueError, match='OTEL_EXPORTER_OTLP_ENDPOINT'):
        configure_tracing(settings)


@pytest.mark.parametrize('sample_ratio', [-0.1, 1.1])
def test_tracing_rejects_invalid_sample_ratio(sample_ratio: float):
    settings = Settings(
        tracing_enabled=True,
        otel_exporter_otlp_endpoint='http://collector:4318/v1/traces',
        otel_sample_ratio=sample_ratio,
    )

    with pytest.raises(ValueError, match='OTEL_SAMPLE_RATIO'):
        configure_tracing(settings)
