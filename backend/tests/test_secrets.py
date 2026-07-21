from pathlib import Path

import pytest

from app.core.config import Settings
from app.core.secrets import SecretConfigurationError, get_secret


def clear_secret_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for env_name in ('OPENAI_API_KEY', 'POLYGON_API_KEY', 'FINNHUB_API_KEY', 'ALPHAVANTAGE_API_KEY'):
        monkeypatch.delenv(env_name, raising=False)


def test_direct_secret_value_is_used_first(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    clear_secret_env(monkeypatch)
    settings = Settings(
        _env_file=None,
        polygon_api_key='direct-key',
        secret_provider='file',
        secrets_dir=str(tmp_path),
        polygon_api_key_secret_name='polygon_key',
    )
    (tmp_path / 'polygon_key').write_text('file-key', encoding='utf-8')

    assert get_secret(settings, 'polygon_api_key') == 'direct-key'


def test_file_secret_provider_reads_named_secret(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    clear_secret_env(monkeypatch)
    settings = Settings(
        _env_file=None,
        secret_provider='file',
        secrets_dir=str(tmp_path),
        polygon_api_key_secret_name='polygon_key',
    )
    (tmp_path / 'polygon_key').write_text('file-key\n', encoding='utf-8')

    assert get_secret(settings, 'polygon_api_key') == 'file-key'


def test_file_secret_provider_returns_none_when_secret_is_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    clear_secret_env(monkeypatch)
    settings = Settings(
        _env_file=None,
        secret_provider='file',
        secrets_dir=str(tmp_path),
        polygon_api_key_secret_name='missing_key',
    )

    assert get_secret(settings, 'polygon_api_key') is None


def test_rejects_unknown_secret_field(monkeypatch: pytest.MonkeyPatch):
    clear_secret_env(monkeypatch)
    settings = Settings(_env_file=None)

    with pytest.raises(SecretConfigurationError):
        get_secret(settings, 'not_a_secret')


def test_rejects_unsupported_secret_provider(monkeypatch: pytest.MonkeyPatch):
    clear_secret_env(monkeypatch)
    settings = Settings(_env_file=None, secret_provider='vault')

    with pytest.raises(SecretConfigurationError):
        get_secret(settings, 'polygon_api_key')
