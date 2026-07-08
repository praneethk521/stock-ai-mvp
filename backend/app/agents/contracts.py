from typing import Any, Literal

from pydantic import BaseModel, Field


class EmptyInput(BaseModel):
    pass


class TickerInput(BaseModel):
    ticker: str = Field(pattern=r'^[A-Za-z0-9.\-]{1,12}$')


class LargeCapMoversInput(BaseModel):
    min_market_cap: float = Field(default=50_000_000_000, ge=0)


class TopMoversInput(BaseModel):
    direction: Literal['gainers', 'losers'] = 'gainers'
    limit: int = Field(default=10, ge=1, le=50)


class RecentItemsInput(BaseModel):
    ticker: str | None = Field(default=None, pattern=r'^[A-Za-z0-9.\-]{1,12}$')
    limit: int = Field(default=20, ge=1, le=100)


class CandlesInput(TickerInput):
    days: int = Field(default=90, ge=20, le=365)


class WatchlistUpsertInput(TickerInput):
    notes: str = Field(default='', max_length=500)


class ToolContract(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    read_only: bool = True
    requires_confirmation: bool = False
    audit_event: str


class ToolEnvelope(BaseModel):
    ok: bool
    data: dict[str, Any] | list[Any] | None = None
    error: dict[str, Any] | None = None


def contract_for(
    name: str,
    description: str,
    input_model: type[BaseModel],
    read_only: bool = True,
    requires_confirmation: bool = False,
) -> ToolContract:
    return ToolContract(
        name=name,
        description=description,
        input_schema=input_model.model_json_schema(),
        output_schema=ToolEnvelope.model_json_schema(),
        read_only=read_only,
        requires_confirmation=requires_confirmation,
        audit_event=f'agent.tool.{name}',
    )


TOOL_CONTRACTS = [
    contract_for('get_market_overview', 'Return current market overview from the active provider.', EmptyInput),
    contract_for('get_large_cap_movers', 'Return tracked large-cap movers above a market-cap threshold.', LargeCapMoversInput),
    contract_for('get_top_market_movers', 'Return top market gainers or losers from the active provider.', TopMoversInput),
    contract_for('get_ticker_snapshot', 'Return provider snapshot and technical signals for a ticker.', TickerInput),
    contract_for('get_historical_candles', 'Return daily OHLCV candles for a ticker.', CandlesInput),
    contract_for('get_company_news', 'Fetch and persist provider news articles for a ticker.', TickerInput),
    contract_for('get_recent_news', 'Return persisted news article audit history.', RecentItemsInput),
    contract_for('generate_recommendation', 'Generate and persist an informational recommendation for a ticker.', TickerInput),
    contract_for('list_recent_recommendations', 'Return persisted recommendation history.', RecentItemsInput),
    contract_for('list_watchlist', 'Return saved watchlist tickers.', EmptyInput),
    contract_for(
        'upsert_watchlist_item',
        'Create or update a watchlist ticker.',
        WatchlistUpsertInput,
        read_only=False,
        requires_confirmation=True,
    ),
    contract_for(
        'delete_watchlist_item',
        'Remove a ticker from the watchlist.',
        TickerInput,
        read_only=False,
        requires_confirmation=True,
    ),
]


def list_tool_contracts() -> list[ToolContract]:
    return TOOL_CONTRACTS


def get_tool_contract(name: str) -> ToolContract | None:
    return next((contract for contract in TOOL_CONTRACTS if contract.name == name), None)
