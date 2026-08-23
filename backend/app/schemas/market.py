from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class MarketMover(BaseModel):
    ticker: str
    company_name: str
    price: float
    change_percent: float
    volume: int
    market_cap: float


class StockCandle(BaseModel):
    ticker: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: float | None = None
    transactions: int | None = None


class ApiErrorBody(BaseModel):
    code: str
    message: str
    status_code: int
    request_id: str | None = None
    details: Any | None = None


class ApiErrorResponse(BaseModel):
    error: ApiErrorBody


class NewsArticle(BaseModel):
    ticker: str
    title: str
    source: str
    url: str
    published_at: datetime
    sentiment: str = Field(pattern='^(positive|neutral|negative)$')
    sentiment_score: float


class NewsSentimentItem(BaseModel):
    ticker: str
    average_sentiment_score: float
    sentiment: str
    article_count: int
    articles: list[NewsArticle]


class NewsArticleHistoryItem(BaseModel):
    id: int
    ticker: str
    title: str
    source: str
    url: str
    published_at: datetime
    sentiment: str
    sentiment_score: float
    provider: str
    first_seen_at: datetime
    last_seen_at: datetime


class Recommendation(BaseModel):
    ticker: str
    recommendation: str
    trade_horizon: str
    confidence_score: float
    risk_score: float
    explanation: str
    supporting_signals: dict
    timestamp: datetime
    model_version: str = 'rules-v1'
    disclaimer: str = 'Informational only. Not financial advice.'


class ExplanationResponse(BaseModel):
    ticker: str
    recommendation: str
    narrative: str
    signal_summary: list[str]
    risk_notes: list[str]
    generated_at: datetime
    model_version: str
    provider: str
    disclaimer: str = 'Informational only. Not financial advice.'


class RecommendationHistoryItem(BaseModel):
    id: int
    ticker: str
    recommendation: str
    trade_horizon: str
    confidence_score: float
    risk_score: float
    explanation: str
    supporting_signals: dict
    generated_at: datetime
    created_at: datetime
    model_version: str


class WatchlistItemCreate(BaseModel):
    ticker: str
    notes: str = Field(default='', max_length=500)


class WatchlistItemRead(BaseModel):
    id: int
    ticker: str
    notes: str
    created_at: datetime


class PriceAlertCreate(BaseModel):
    ticker: str
    condition: Literal['above', 'below']
    target_price: float = Field(gt=0, le=1_000_000_000)


class PriceAlertUpdate(BaseModel):
    condition: Literal['above', 'below'] | None = None
    target_price: float | None = Field(default=None, gt=0, le=1_000_000_000)
    is_active: bool | None = None


class PriceAlertRead(BaseModel):
    id: int
    ticker: str
    condition: str
    target_price: float
    is_active: bool
    last_price: float | None
    triggered_at: datetime | None
    created_at: datetime
    updated_at: datetime


class BacktestRequest(BaseModel):
    ticker: str
    days: int = Field(default=180, ge=20, le=365)
    initial_capital: float = Field(default=10_000, ge=100, le=1_000_000_000)
    fast_window: int = Field(default=10, ge=2, le=100)
    slow_window: int = Field(default=30, ge=3, le=200)
    fee_bps: float = Field(default=5, ge=0, le=100)

    @model_validator(mode='after')
    def validate_windows(self) -> 'BacktestRequest':
        if self.fast_window >= self.slow_window:
            raise ValueError('fast_window must be less than slow_window')
        if self.days <= self.slow_window:
            raise ValueError('days must be greater than slow_window')
        return self


class BacktestTrade(BaseModel):
    side: Literal['buy', 'sell']
    signal_timestamp: datetime
    execution_timestamp: datetime
    price: float
    shares: float
    fee: float
    reason: str


class BacktestResponse(BaseModel):
    ticker: str
    strategy: str
    started_at: datetime
    ended_at: datetime
    initial_capital: float
    final_value: float
    total_return_percent: float
    benchmark_return_percent: float
    max_drawdown_percent: float
    trade_count: int
    trades: list[BacktestTrade]
    parameters: dict[str, float | int]
    disclaimer: str = 'Historical simulation only. Past performance does not predict future results.'
