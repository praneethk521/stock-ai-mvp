from fastapi import APIRouter, HTTPException
from app.schemas.market import Recommendation
from app.services.factory import get_market_provider, get_news_provider
from app.services.recommendation_engine import RecommendationEngine

router = APIRouter()
market_provider = get_market_provider()
news_provider = get_news_provider()
engine = RecommendationEngine()


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


@router.get('/stocks/{ticker}')
async def stock_details(ticker: str) -> dict:
    if not ticker.isalnum() or len(ticker) > 12:
        raise HTTPException(status_code=400, detail='Invalid ticker')
    snapshot = await market_provider.get_ticker_snapshot(ticker)
    news = await news_provider.get_company_news(ticker)
    return {'snapshot': snapshot, 'news': news}


@router.get('/stocks/{ticker}/recommendation', response_model=Recommendation)
async def stock_recommendation(ticker: str) -> Recommendation:
    if not ticker.isalnum() or len(ticker) > 12:
        raise HTTPException(status_code=400, detail='Invalid ticker')
    snapshot = await market_provider.get_ticker_snapshot(ticker)
    news = await news_provider.get_company_news(ticker)
    avg_sentiment = sum(a.sentiment_score for a in news) / len(news) if news else 0.0
    return engine.generate(ticker=ticker, snapshot=snapshot, sentiment_score=avg_sentiment)
