from datetime import datetime
from pydantic import BaseModel, Field


class MarketMover(BaseModel):
    ticker: str
    company_name: str
    price: float
    change_percent: float
    volume: int
    market_cap: float


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
