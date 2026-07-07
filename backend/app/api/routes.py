import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.config import get_settings
from app.repositories.recommendations import count_recommendations, create_recommendation_record, list_recent_recommendations
from app.repositories.watchlist import delete_watchlist_item, list_watchlist_items, upsert_watchlist_item
from app.schemas.market import NewsArticle, NewsSentimentItem, Recommendation, RecommendationHistoryItem, StockCandle, WatchlistItemCreate, WatchlistItemRead
from app.services.factory import get_market_provider, get_news_provider
from app.services.recommendation_engine import RecommendationEngine

router = APIRouter()
settings = get_settings()
market_provider = get_market_provider()
news_provider = get_news_provider()
engine = RecommendationEngine()
TICKER_PATTERN = re.compile(r'^[A-Za-z0-9.\-]{1,12}$')
DEFAULT_SENTIMENT_TICKERS = ['NVDA', 'TSLA', 'AAPL', 'MSFT', 'AMZN', 'META', 'AVGO', 'TSM', 'GOOG', 'BRK.B']
TOP_MOVER_DIRECTIONS = {'gainers', 'losers'}


def validate_ticker(ticker: str) -> str:
    if not TICKER_PATTERN.fullmatch(ticker):
        raise HTTPException(status_code=400, detail='Invalid ticker')
    return ticker.upper()


def classify_sentiment(score: float) -> str:
    if score >= 0.25:
        return 'positive'
    if score <= -0.25:
        return 'negative'
    return 'neutral'


def validate_top_mover_direction(direction: str) -> str:
    normalized = direction.lower()
    if normalized not in TOP_MOVER_DIRECTIONS:
        raise HTTPException(status_code=400, detail='Direction must be gainers or losers')
    return normalized


def provider_health(provider: object, name: str) -> dict:
    health_check = getattr(provider, 'health_check', None)
    if callable(health_check):
        try:
            return health_check()
        except Exception as exc:
            return {'provider': name, 'ok': False, 'error': str(exc)}
    return {'provider': name, 'ok': True, 'mode': 'mock'}


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


@router.get('/market/top-movers')
async def top_market_movers(direction: str = 'gainers', limit: int = 10) -> dict:
    normalized_direction = validate_top_mover_direction(direction)
    bounded_limit = min(max(limit, 1), 50)
    try:
        movers = await market_provider.get_top_market_movers(direction=normalized_direction, limit=bounded_limit)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f'Market mover provider failed: {exc}') from exc
    return {'direction': normalized_direction, 'limit': bounded_limit, 'items': movers}


@router.get('/news/sentiment', response_model=list[NewsSentimentItem])
async def news_sentiment(tickers: str | None = None) -> list[NewsSentimentItem]:
    symbols = [validate_ticker(item.strip()) for item in tickers.split(',') if item.strip()] if tickers else DEFAULT_SENTIMENT_TICKERS
    unique_symbols = list(dict.fromkeys(symbols))[:20]
    results: list[NewsSentimentItem] = []
    for symbol in unique_symbols:
        articles: list[NewsArticle] = await news_provider.get_company_news(symbol)
        avg_score = sum(article.sentiment_score for article in articles) / len(articles) if articles else 0.0
        results.append(
            NewsSentimentItem(
                ticker=symbol,
                average_sentiment_score=round(avg_score, 3),
                sentiment=classify_sentiment(avg_score),
                article_count=len(articles),
                articles=articles,
            )
        )
    return results


@router.get('/admin/status')
async def admin_status(db: Session = Depends(get_db)) -> dict:
    return {
        'app_env': settings.app_env,
        'market_data_provider': settings.market_data_provider,
        'news_provider': settings.news_provider,
        'market_provider_health': provider_health(market_provider, settings.market_data_provider),
        'news_provider_health': provider_health(news_provider, settings.news_provider),
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


@router.get('/watchlist', response_model=list[WatchlistItemRead])
async def watchlist(db: Session = Depends(get_db)) -> list[WatchlistItemRead]:
    return list_watchlist_items(db)


@router.post('/watchlist', response_model=WatchlistItemRead)
async def add_watchlist_item(item: WatchlistItemCreate, db: Session = Depends(get_db)) -> WatchlistItemRead:
    symbol = validate_ticker(item.ticker)
    return upsert_watchlist_item(db, ticker=symbol, notes=item.notes.strip())


@router.delete('/watchlist/{ticker}')
async def remove_watchlist_item(ticker: str, db: Session = Depends(get_db)) -> dict:
    symbol = validate_ticker(ticker)
    deleted = delete_watchlist_item(db, ticker=symbol)
    if not deleted:
        raise HTTPException(status_code=404, detail='Watchlist item not found')
    return {'deleted': True, 'ticker': symbol}


@router.get('/stocks/{ticker}')
async def stock_details(ticker: str) -> dict:
    symbol = validate_ticker(ticker)
    snapshot = await market_provider.get_ticker_snapshot(symbol)
    news = await news_provider.get_company_news(symbol)
    return {'snapshot': snapshot, 'news': news}


@router.get('/stocks/{ticker}/candles', response_model=list[StockCandle])
async def stock_candles(ticker: str, days: int = 90) -> list[StockCandle]:
    symbol = validate_ticker(ticker)
    bounded_days = min(max(days, 20), 365)
    return await market_provider.get_historical_candles(symbol, days=bounded_days)


@router.get('/stocks/{ticker}/recommendation', response_model=Recommendation)
async def stock_recommendation(ticker: str, db: Session = Depends(get_db)) -> Recommendation:
    symbol = validate_ticker(ticker)
    snapshot = await market_provider.get_ticker_snapshot(symbol)
    news = await news_provider.get_company_news(symbol)
    avg_sentiment = sum(a.sentiment_score for a in news) / len(news) if news else 0.0
    recommendation = engine.generate(ticker=symbol, snapshot=snapshot, sentiment_score=avg_sentiment)
    create_recommendation_record(db, recommendation)
    return recommendation
