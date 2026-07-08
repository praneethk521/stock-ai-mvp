from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


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
