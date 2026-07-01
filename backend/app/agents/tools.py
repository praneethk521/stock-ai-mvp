from app.services.factory import get_market_provider, get_news_provider
from app.services.recommendation_engine import RecommendationEngine


async def get_large_cap_movers_tool(min_market_cap: float = 50_000_000_000) -> dict:
    provider = get_market_provider()
    movers = await provider.get_large_cap_movers(min_market_cap)
    return {'items': [m.model_dump() for m in movers]}


async def generate_recommendation_tool(ticker: str) -> dict:
    market = get_market_provider()
    news_provider = get_news_provider()
    snapshot = await market.get_ticker_snapshot(ticker)
    news = await news_provider.get_company_news(ticker)
    avg_sentiment = sum(a.sentiment_score for a in news) / len(news) if news else 0.0
    return RecommendationEngine().generate(ticker, snapshot, avg_sentiment).model_dump()
