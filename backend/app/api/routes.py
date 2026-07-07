import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.config import get_settings
from app.repositories.recommendations import count_recommendations, create_recommendation_record, list_recent_recommendations
from app.schemas.market import Recommendation, RecommendationHistoryItem
from app.services.factory import get_market_provider, get_news_provider
from app.services.recommendation_engine import RecommendationEngine

router = APIRouter()
settings = get_settings()
market_provider = get_market_provider()
news_provider = get_news_provider()
engine = RecommendationEngine()
TICKER_PATTERN = re.compile(r'^[A-Za-z0-9.\-]{1,12}$')


def validate_ticker(ticker: str) -> str:
    if not TICKER_PATTERN.fullmatch(ticker):
        raise HTTPException(status_code=400, detail='Invalid ticker')
    return ticker.upper()


@router.get('/health')
async def health() -> dict:
    return {'status': 'ok'}


@router.get('/market/overview')
async def market_overview() -> dict:
    return await market_provider.get_market_overview()


@router.get('/market/large-cap-movers')
async def large_cap_movers(min_market_cap: float = 50_000_000_000) -> dict:
    movers = await market_provider.get_large_cap_movers(min_market_cap=min_market_cap)
    return {'min_market_cap': min_market_cap, 'items': movers}


@router.get('/admin/status')
async def admin_status(db: Session = Depends(get_db)) -> dict:
    return {
        'app_env': settings.app_env,
        'market_data_provider': settings.market_data_provider,
        'news_provider': settings.news_provider,
        'recommendation_model': engine.model_version,
        'persisted_recommendations': count_recommendations(db),
        'disclaimer': 'Informational only. Not financial advice.',
    }


@router.get('/recommendations/recent', response_model=list[RecommendationHistoryItem])
async def recent_recommendations(
    ticker: str | None = None,
    limit: int = 20,
    db: Session = Depends(get_db),
) -> list[RecommendationHistoryItem]:
    symbol = validate_ticker(ticker) if ticker else None
    bounded_limit = min(max(limit, 1), 100)
    return list_recent_recommendations(db, ticker=symbol, limit=bounded_limit)


@router.get('/stocks/{ticker}')
async def stock_details(ticker: str) -> dict:
    symbol = validate_ticker(ticker)
    snapshot = await market_provider.get_ticker_snapshot(symbol)
    news = await news_provider.get_company_news(symbol)
    return {'snapshot': snapshot, 'news': news}


@router.get('/stocks/{ticker}/recommendation', response_model=Recommendation)
async def stock_recommendation(ticker: str, db: Session = Depends(get_db)) -> Recommendation:
    symbol = validate_ticker(ticker)
    snapshot = await market_provider.get_ticker_snapshot(symbol)
    news = await news_provider.get_company_news(symbol)
    avg_sentiment = sum(a.sentiment_score for a in news) / len(news) if news else 0.0
    recommendation = engine.generate(ticker=symbol, snapshot=snapshot, sentiment_score=avg_sentiment)
    create_recommendation_record(db, recommendation)
    return recommendation
