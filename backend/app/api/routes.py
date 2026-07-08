import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.contracts import ToolContract, ToolEnvelope, list_tool_contracts
from app.agents.orchestrator import AgentToolOrchestrator
from app.core.db import get_db
from app.core.config import get_settings
from app.repositories.agent_audit import count_agent_tool_audit_logs, list_agent_tool_audit_logs
from app.repositories.news import count_news_articles, list_recent_news_articles, persist_news_articles
from app.repositories.recommendations import count_recommendations, create_recommendation_record, list_recent_recommendations
from app.repositories.watchlist import delete_watchlist_item, list_watchlist_items, upsert_watchlist_item
from app.schemas.agent import AgentToolAuditItem, AgentToolExecutionRequest
from app.schemas.market import ApiErrorResponse, ExplanationResponse, NewsArticle, NewsArticleHistoryItem, NewsSentimentItem, Recommendation, RecommendationHistoryItem, StockCandle, WatchlistItemCreate, WatchlistItemRead
from app.services.explanation_service import ExplanationService
from app.services.factory import get_market_provider, get_news_provider
from app.services.recommendation_engine import RecommendationEngine

COMMON_ERROR_RESPONSES = {
    400: {'description': 'Bad request', 'model': ApiErrorResponse},
    404: {'description': 'Resource not found', 'model': ApiErrorResponse},
    422: {'description': 'Request validation failed', 'model': ApiErrorResponse},
    429: {'description': 'Rate limit exceeded', 'model': ApiErrorResponse},
    500: {'description': 'Unexpected server error', 'model': ApiErrorResponse},
}
router = APIRouter(responses=COMMON_ERROR_RESPONSES)
settings = get_settings()
market_provider = get_market_provider()
news_provider = get_news_provider()
engine = RecommendationEngine()
explanation_service = ExplanationService()
agent_orchestrator = AgentToolOrchestrator(
    market_provider=market_provider,
    news_provider=news_provider,
    recommendation_engine=engine,
    news_provider_name=settings.news_provider,
)
TICKER_PATTERN = re.compile(r'^[A-Za-z0-9.\-]{1,12}$')
DEFAULT_SENTIMENT_TICKERS = ['NVDA', 'TSLA', 'AAPL', 'MSFT', 'AMZN', 'META', 'AVGO', 'TSM', 'GOOG', 'BRK.B']
TOP_MOVER_DIRECTIONS = {'gainers', 'losers'}
PROVIDER_ERROR_RESPONSES = {
    502: {
        'description': 'Upstream market/news provider failure',
        'model': ApiErrorResponse,
    }
}


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


async def fetch_and_persist_news(symbol: str, db: Session) -> list[NewsArticle]:
    articles: list[NewsArticle] = await news_provider.get_company_news(symbol)
    persist_news_articles(db, articles, provider=settings.news_provider)
    return articles


@router.get('/health')
async def health() -> dict:
    return {'status': 'ok'}


@router.get('/market/overview', responses=PROVIDER_ERROR_RESPONSES)
async def market_overview() -> dict:
    return await market_provider.get_market_overview()


@router.get('/market/large-cap-movers', responses=PROVIDER_ERROR_RESPONSES)
async def large_cap_movers(min_market_cap: float = 50_000_000_000) -> dict:
    movers = await market_provider.get_large_cap_movers(min_market_cap=min_market_cap)
    return {'min_market_cap': min_market_cap, 'items': movers}


@router.get('/market/top-movers', responses=PROVIDER_ERROR_RESPONSES)
async def top_market_movers(direction: str = 'gainers', limit: int = 10) -> dict:
    normalized_direction = validate_top_mover_direction(direction)
    bounded_limit = min(max(limit, 1), 50)
    try:
        movers = await market_provider.get_top_market_movers(direction=normalized_direction, limit=bounded_limit)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f'Market mover provider failed: {exc}') from exc
    return {'direction': normalized_direction, 'limit': bounded_limit, 'items': movers}


@router.get('/news/sentiment', response_model=list[NewsSentimentItem], responses=PROVIDER_ERROR_RESPONSES)
async def news_sentiment(tickers: str | None = None, db: Session = Depends(get_db)) -> list[NewsSentimentItem]:
    symbols = [validate_ticker(item.strip()) for item in tickers.split(',') if item.strip()] if tickers else DEFAULT_SENTIMENT_TICKERS
    unique_symbols = list(dict.fromkeys(symbols))[:20]
    results: list[NewsSentimentItem] = []
    for symbol in unique_symbols:
        articles = await fetch_and_persist_news(symbol, db)
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
        'persisted_news_articles': count_news_articles(db),
        'agent_tool_audit_events': count_agent_tool_audit_logs(db),
        'disclaimer': 'Informational only. Not financial advice.',
    }


@router.get('/agent/tool-contracts', response_model=list[ToolContract])
async def agent_tool_contracts() -> list[ToolContract]:
    return list_tool_contracts()


@router.get('/agent/audit-log', response_model=list[AgentToolAuditItem])
async def agent_audit_log(
    tool_name: str | None = None,
    limit: int = 20,
    db: Session = Depends(get_db),
) -> list[AgentToolAuditItem]:
    bounded_limit = min(max(limit, 1), 100)
    return list_agent_tool_audit_logs(db, tool_name=tool_name, limit=bounded_limit)


@router.post('/agent/tools/{tool_name}/execute', response_model=ToolEnvelope)
async def execute_agent_tool(
    tool_name: str,
    request: AgentToolExecutionRequest,
    db: Session = Depends(get_db),
) -> ToolEnvelope:
    return await agent_orchestrator.execute(
        db,
        tool_name=tool_name,
        input_payload=request.input,
        confirmed=request.confirmed,
    )


@router.get('/recommendations/recent', response_model=list[RecommendationHistoryItem])
async def recent_recommendations(
    ticker: str | None = None,
    limit: int = 20,
    db: Session = Depends(get_db),
) -> list[RecommendationHistoryItem]:
    symbol = validate_ticker(ticker) if ticker else None
    bounded_limit = min(max(limit, 1), 100)
    return list_recent_recommendations(db, ticker=symbol, limit=bounded_limit)


@router.get('/news/recent', response_model=list[NewsArticleHistoryItem])
async def recent_news(
    ticker: str | None = None,
    limit: int = 20,
    db: Session = Depends(get_db),
) -> list[NewsArticleHistoryItem]:
    symbol = validate_ticker(ticker) if ticker else None
    bounded_limit = min(max(limit, 1), 100)
    return list_recent_news_articles(db, ticker=symbol, limit=bounded_limit)


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


@router.get('/stocks/{ticker}', responses=PROVIDER_ERROR_RESPONSES)
async def stock_details(ticker: str, db: Session = Depends(get_db)) -> dict:
    symbol = validate_ticker(ticker)
    snapshot = await market_provider.get_ticker_snapshot(symbol)
    news = await fetch_and_persist_news(symbol, db)
    return {'snapshot': snapshot, 'news': news}


@router.get('/stocks/{ticker}/candles', response_model=list[StockCandle], responses=PROVIDER_ERROR_RESPONSES)
async def stock_candles(ticker: str, days: int = 90) -> list[StockCandle]:
    symbol = validate_ticker(ticker)
    bounded_days = min(max(days, 20), 365)
    return await market_provider.get_historical_candles(symbol, days=bounded_days)


@router.get('/stocks/{ticker}/recommendation', response_model=Recommendation, responses=PROVIDER_ERROR_RESPONSES)
async def stock_recommendation(ticker: str, db: Session = Depends(get_db)) -> Recommendation:
    symbol = validate_ticker(ticker)
    snapshot = await market_provider.get_ticker_snapshot(symbol)
    news = await fetch_and_persist_news(symbol, db)
    avg_sentiment = sum(a.sentiment_score for a in news) / len(news) if news else 0.0
    recommendation = engine.generate(ticker=symbol, snapshot=snapshot, sentiment_score=avg_sentiment)
    create_recommendation_record(db, recommendation)
    return recommendation


@router.get('/stocks/{ticker}/explanation', response_model=ExplanationResponse, responses=PROVIDER_ERROR_RESPONSES)
async def stock_explanation(ticker: str, db: Session = Depends(get_db)) -> ExplanationResponse:
    symbol = validate_ticker(ticker)
    snapshot = await market_provider.get_ticker_snapshot(symbol)
    news = await fetch_and_persist_news(symbol, db)
    avg_sentiment = sum(article.sentiment_score for article in news) / len(news) if news else 0.0
    recommendation = engine.generate(ticker=symbol, snapshot=snapshot, sentiment_score=avg_sentiment)
    return explanation_service.generate(symbol, recommendation, snapshot, avg_sentiment)
