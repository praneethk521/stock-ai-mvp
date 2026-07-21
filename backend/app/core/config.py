from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    app_env: str = 'local'
    app_name: str = 'Stock AI MVP'
    api_v1_prefix: str = '/api/v1'
    database_url: str = Field(default='postgresql+psycopg://stock:stock@localhost:5432/stock_ai')
    redis_url: str = 'redis://localhost:6379/0'
    cors_origins: str = 'http://localhost:3000'
    default_user_id: str = 'local-demo-user'
    auth_mode: str = 'local'
    auth_user_id_claim: str = 'sub'
    auth_jwt_algorithm: str = 'HS256'
    auth_jwt_audience: str | None = None
    auth_jwt_issuer: str | None = None
    auth_jwt_jwks_url: str | None = None
    auth_jwt_secret: str | None = None
    auth_jwt_secret_name: str | None = None
    market_data_provider: str = 'mock'
    news_provider: str = 'mock'
    polygon_base_url: str = 'https://api.polygon.io'
    provider_timeout_seconds: float = 10.0
    provider_cache_ttl_seconds: int = 30
    provider_retry_count: int = 2
    secret_provider: str = 'env'
    secrets_dir: str = '/run/secrets'
    openai_api_key: str | None = None
    polygon_api_key: str | None = None
    finnhub_api_key: str | None = None
    alphavantage_api_key: str | None = None
    openai_api_key_secret_name: str | None = None
    polygon_api_key_secret_name: str | None = None
    finnhub_api_key_secret_name: str | None = None
    alphavantage_api_key_secret_name: str | None = None

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(',') if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
