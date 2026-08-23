from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.schemas.market import BacktestRequest, StockCandle
from app.services.backtest_service import BacktestService


def candles_from_prices(prices: list[float]) -> list[StockCandle]:
    started_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return [
        StockCandle(
            ticker='TEST',
            timestamp=started_at + timedelta(days=index),
            open=price - 0.5,
            high=price + 1,
            low=price - 1,
            close=price,
            volume=1_000,
        )
        for index, price in enumerate(prices)
    ]


def test_backtest_executes_signal_at_next_candle_open():
    candles = candles_from_prices([10, 9, 8, 9, 11, 12, 10, 8])
    request = BacktestRequest(ticker='TEST', days=20, fast_window=2, slow_window=3, fee_bps=0)

    result = BacktestService().run(candles, request)

    buy = result.trades[0]
    assert buy.side == 'buy'
    assert buy.signal_timestamp == candles[4].timestamp
    assert buy.execution_timestamp == candles[5].timestamp
    assert buy.price == candles[5].open
    assert result.trades[-1].reason == 'end_of_period_liquidation'
    assert result.trade_count == 1
    assert result.total_return_percent < 0
    assert result.max_drawdown_percent > 0


def test_backtest_applies_transaction_fees():
    candles = candles_from_prices([8, 9, 10, 11, 12, 13])
    no_fee = BacktestService().run(
        candles,
        BacktestRequest(ticker='TEST', days=20, fast_window=2, slow_window=3, fee_bps=0),
    )
    with_fee = BacktestService().run(
        candles,
        BacktestRequest(ticker='TEST', days=20, fast_window=2, slow_window=3, fee_bps=50),
    )

    assert with_fee.final_value < no_fee.final_value
    assert sum(trade.fee for trade in with_fee.trades) > 0


def test_backtest_rejects_invalid_windows():
    with pytest.raises(ValidationError, match='fast_window must be less than slow_window'):
        BacktestRequest(ticker='TEST', days=30, fast_window=10, slow_window=10)
