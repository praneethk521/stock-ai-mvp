from pathlib import Path

from app.core.config import Settings


SECRET_ENV_VARS = {
    'openai_api_key': 'OPENAI_API_KEY',
    'polygon_api_key': 'POLYGON_API_KEY',
    'finnhub_api_key': 'FINNHUB_API_KEY',
    'alphavantage_api_key': 'ALPHAVANTAGE_API_KEY',
    'auth_jwt_secret': 'AUTH_JWT_SECRET',
}

SECRET_NAME_FIELDS = {
    'openai_api_key': 'openai_api_key_secret_name',
    'polygon_api_key': 'polygon_api_key_secret_name',
    'finnhub_api_key': 'finnhub_api_key_secret_name',
    'alphavantage_api_key': 'alphavantage_api_key_secret_name',
    'auth_jwt_secret': 'auth_jwt_secret_name',
}


class SecretConfigurationError(ValueError):
    pass


def get_secret(settings: Settings, field_name: str) -> str | None:
    if field_name not in SECRET_ENV_VARS:
        raise SecretConfigurationError(f'Unknown secret field: {field_name}')

    direct_value = getattr(settings, field_name)
    if direct_value:
        return direct_value

    if settings.secret_provider == 'env':
        return None

    if settings.secret_provider == 'file':
        secret_name = getattr(settings, SECRET_NAME_FIELDS[field_name]) or SECRET_ENV_VARS[field_name]
        secret_path = Path(settings.secrets_dir) / secret_name
        if not secret_path.exists():
            return None
        value = secret_path.read_text(encoding='utf-8').strip()
        return value or None

    raise SecretConfigurationError(f'Unsupported secret provider: {settings.secret_provider}')
