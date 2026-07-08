from time import perf_counter

from sqlalchemy.orm import Session

from app.repositories.agent_audit import create_agent_tool_audit_log
from app.services.factory import get_market_provider, get_news_provider
from app.services.recommendation_engine import RecommendationEngine


def _duration_ms(started_at: float) -> int:
    return int((perf_counter() - started_at) * 1000)


async def get_large_cap_movers_tool(min_market_cap: float = 50_000_000_000, db: Session | None = None) -> dict:
    started_at = perf_counter()
    provider = get_market_provider()
    try:
        movers = await provider.get_large_cap_movers(min_market_cap)
        result = {'items': [m.model_dump() for m in movers]}
        if db:
            create_agent_tool_audit_log(
                db,
                tool_name='get_large_cap_movers',
                input_payload={'min_market_cap': min_market_cap},
                ok=True,
                output_summary={'item_count': len(result['items'])},
                duration_ms=_duration_ms(started_at),
            )
        return result
    except Exception as exc:
        if db:
            create_agent_tool_audit_log(
                db,
                tool_name='get_large_cap_movers',
                input_payload={'min_market_cap': min_market_cap},
                ok=False,
                error={'message': str(exc), 'type': type(exc).__name__},
                duration_ms=_duration_ms(started_at),
            )
        raise


async def generate_recommendation_tool(ticker: str, db: Session | None = None) -> dict:
    started_at = perf_counter()
    market = get_market_provider()
    news_provider = get_news_provider()
    try:
        snapshot = await market.get_ticker_snapshot(ticker)
        news = await news_provider.get_company_news(ticker)
        avg_sentiment = sum(a.sentiment_score for a in news) / len(news) if news else 0.0
        recommendation = RecommendationEngine().generate(ticker, snapshot, avg_sentiment).model_dump()
        if db:
            create_agent_tool_audit_log(
                db,
                tool_name='generate_recommendation',
                input_payload={'ticker': ticker.upper()},
                ok=True,
                output_summary={
                    'ticker': recommendation['ticker'],
                    'recommendation': recommendation['recommendation'],
                    'confidence_score': recommendation['confidence_score'],
                },
                duration_ms=_duration_ms(started_at),
            )
        return recommendation
    except Exception as exc:
        if db:
            create_agent_tool_audit_log(
                db,
                tool_name='generate_recommendation',
                input_payload={'ticker': ticker.upper()},
                ok=False,
                error={'message': str(exc), 'type': type(exc).__name__},
                duration_ms=_duration_ms(started_at),
            )
        raise
