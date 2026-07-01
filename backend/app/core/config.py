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
    market_data_provider: str = 'mock'
    news_provider: str = 'mock'
    openai_api_key: str | None = None
    polygon_api_key: str | None = None
    finnhub_api_key: str | None = None
    alphavantage_api_key: str | None = None

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(',') if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
