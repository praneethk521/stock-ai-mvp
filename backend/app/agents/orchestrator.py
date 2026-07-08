from time import perf_counter
from typing import Any

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.agents.contracts import ToolEnvelope, get_tool_contract, get_tool_input_model
from app.providers.news import NewsProvider
from app.providers.market_data import MarketDataProvider
from app.repositories.agent_audit import create_agent_tool_audit_log
from app.repositories.news import list_recent_news_articles, persist_news_articles
from app.repositories.recommendations import create_recommendation_record, list_recent_recommendations
from app.repositories.watchlist import delete_watchlist_item, list_watchlist_items, upsert_watchlist_item
from app.services.recommendation_engine import RecommendationEngine


class AgentToolError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


class AgentToolOrchestrator:
    def __init__(
        self,
        market_provider: MarketDataProvider,
        news_provider: NewsProvider,
        recommendation_engine: RecommendationEngine,
        news_provider_name: str,
    ) -> None:
        self.market_provider = market_provider
        self.news_provider = news_provider
        self.recommendation_engine = recommendation_engine
        self.news_provider_name = news_provider_name

    async def execute(
        self,
        db: Session,
        tool_name: str,
        input_payload: dict[str, Any] | None = None,
        confirmed: bool = False,
    ) -> ToolEnvelope:
        started_at = perf_counter()
        payload = input_payload or {}
        try:
            contract = get_tool_contract(tool_name)
            input_model = get_tool_input_model(tool_name)
            if not contract or not input_model:
                raise AgentToolError('unknown_tool', f'Unknown tool: {tool_name}')
            if contract.requires_confirmation and not confirmed:
                raise AgentToolError('confirmation_required', f'{tool_name} requires confirmation')

            validated = input_model.model_validate(payload)
            data = await self._dispatch(db, tool_name, validated.model_dump())
            envelope = ToolEnvelope(ok=True, data=data)
            create_agent_tool_audit_log(
                db,
                tool_name=tool_name,
                input_payload=validated.model_dump(),
                ok=True,
                output_summary=self._summarize(data),
                duration_ms=self._duration_ms(started_at),
            )
            return envelope
        except ValidationError as exc:
            return self._record_error(db, tool_name, payload, started_at, 'validation_error', exc.errors())
        except AgentToolError as exc:
            return self._record_error(db, tool_name, payload, started_at, exc.code, str(exc))
        except Exception as exc:
            return self._record_error(db, tool_name, payload, started_at, 'tool_execution_failed', str(exc))

    async def _dispatch(self, db: Session, tool_name: str, payload: dict[str, Any]) -> dict[str, Any] | list[Any]:
        if tool_name == 'get_market_overview':
            return await self.market_provider.get_market_overview()
        if tool_name == 'get_large_cap_movers':
            movers = await self.market_provider.get_large_cap_movers(payload['min_market_cap'])
            return {'items': [item.model_dump() for item in movers]}
        if tool_name == 'get_top_market_movers':
            movers = await self.market_provider.get_top_market_movers(payload['direction'], payload['limit'])
            return {'items': [item.model_dump() for item in movers]}
        if tool_name == 'get_ticker_snapshot':
            return await self.market_provider.get_ticker_snapshot(payload['ticker'])
        if tool_name == 'get_historical_candles':
            candles = await self.market_provider.get_historical_candles(payload['ticker'], payload['days'])
            return {'items': [item.model_dump() for item in candles]}
        if tool_name == 'get_company_news':
            articles = await self.news_provider.get_company_news(payload['ticker'])
            persist_news_articles(db, articles, provider=self.news_provider_name)
            return {'items': [item.model_dump() for item in articles]}
        if tool_name == 'get_recent_news':
            return {'items': [self._model_dict(item) for item in list_recent_news_articles(db, payload.get('ticker'), payload['limit'])]}
        if tool_name == 'generate_recommendation':
            snapshot = await self.market_provider.get_ticker_snapshot(payload['ticker'])
            articles = await self.news_provider.get_company_news(payload['ticker'])
            persist_news_articles(db, articles, provider=self.news_provider_name)
            avg_sentiment = sum(item.sentiment_score for item in articles) / len(articles) if articles else 0.0
            recommendation = self.recommendation_engine.generate(payload['ticker'], snapshot, avg_sentiment)
            create_recommendation_record(db, recommendation)
            return recommendation.model_dump()
        if tool_name == 'list_recent_recommendations':
            return {'items': [self._model_dict(item) for item in list_recent_recommendations(db, payload.get('ticker'), payload['limit'])]}
        if tool_name == 'list_watchlist':
            return {'items': [self._model_dict(item) for item in list_watchlist_items(db)]}
        if tool_name == 'upsert_watchlist_item':
            return self._model_dict(upsert_watchlist_item(db, payload['ticker'].upper(), payload['notes'].strip()))
        if tool_name == 'delete_watchlist_item':
            deleted = delete_watchlist_item(db, payload['ticker'].upper())
            return {'deleted': deleted, 'ticker': payload['ticker'].upper()}
        raise AgentToolError('unknown_tool', f'Unknown tool: {tool_name}')

    def _record_error(
        self,
        db: Session,
        tool_name: str,
        payload: dict[str, Any],
        started_at: float,
        code: str,
        detail: Any,
    ) -> ToolEnvelope:
        error = {'code': code, 'detail': detail}
        create_agent_tool_audit_log(
            db,
            tool_name=tool_name,
            input_payload=payload,
            ok=False,
            error=error,
            duration_ms=self._duration_ms(started_at),
        )
        return ToolEnvelope(ok=False, error=error)

    def _summarize(self, data: dict[str, Any] | list[Any]) -> dict[str, Any]:
        if isinstance(data, list):
            return {'item_count': len(data)}
        if isinstance(data.get('items'), list):
            return {'item_count': len(data['items'])}
        return {key: data[key] for key in ['ticker', 'recommendation', 'deleted'] if key in data}

    def _model_dict(self, item: Any) -> dict[str, Any]:
        return {column.name: getattr(item, column.name) for column in item.__table__.columns}

    def _duration_ms(self, started_at: float) -> int:
        return int((perf_counter() - started_at) * 1000)
