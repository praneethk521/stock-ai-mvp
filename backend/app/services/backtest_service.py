from datetime import datetime

from app.schemas.market import BacktestRequest, BacktestResponse, BacktestTrade, StockCandle


class BacktestService:
    strategy_name = 'sma-crossover-v1'

    def run(self, candles: list[StockCandle], request: BacktestRequest) -> BacktestResponse:
        ordered = sorted(candles, key=lambda candle: candle.timestamp)
        if len(ordered) <= request.slow_window:
            raise ValueError('Not enough historical candles for the selected slow window')

        fee_rate = request.fee_bps / 10_000
        cash = request.initial_capital
        shares = 0.0
        closes: list[float] = []
        equity_curve: list[float] = []
        trades: list[BacktestTrade] = []
        pending_action: tuple[str, datetime, str] | None = None
        previous_fast: float | None = None
        previous_slow: float | None = None

        for index, candle in enumerate(ordered):
            if pending_action is not None:
                action, signal_timestamp, reason = pending_action
                if action == 'buy' and shares == 0:
                    notional = cash / (1 + fee_rate)
                    fee = notional * fee_rate
                    shares = notional / candle.open
                    cash = max(cash - notional - fee, 0)
                    trades.append(
                        BacktestTrade(
                            side='buy',
                            signal_timestamp=signal_timestamp,
                            execution_timestamp=candle.timestamp,
                            price=round(candle.open, 4),
                            shares=round(shares, 6),
                            fee=round(fee, 4),
                            reason=reason,
                        )
                    )
                elif action == 'sell' and shares > 0:
                    sold_shares = shares
                    notional = sold_shares * candle.open
                    fee = notional * fee_rate
                    cash += notional - fee
                    shares = 0
                    trades.append(
                        BacktestTrade(
                            side='sell',
                            signal_timestamp=signal_timestamp,
                            execution_timestamp=candle.timestamp,
                            price=round(candle.open, 4),
                            shares=round(sold_shares, 6),
                            fee=round(fee, 4),
                            reason=reason,
                        )
                    )
                pending_action = None

            closes.append(candle.close)
            equity_curve.append(cash + shares * candle.close)

            if index < request.slow_window - 1 or index == len(ordered) - 1:
                continue

            fast_sma = sum(closes[-request.fast_window :]) / request.fast_window
            slow_sma = sum(closes[-request.slow_window :]) / request.slow_window
            if previous_fast is None or previous_slow is None:
                bullish_entry = fast_sma > slow_sma
                bullish_cross = False
                bearish_cross = False
            else:
                bullish_entry = False
                bullish_cross = previous_fast <= previous_slow and fast_sma > slow_sma
                bearish_cross = previous_fast >= previous_slow and fast_sma < slow_sma

            if shares == 0 and (bullish_entry or bullish_cross):
                pending_action = ('buy', candle.timestamp, 'fast_sma_crossed_above_slow_sma')
            elif shares > 0 and bearish_cross:
                pending_action = ('sell', candle.timestamp, 'fast_sma_crossed_below_slow_sma')

            previous_fast = fast_sma
            previous_slow = slow_sma

        final_candle = ordered[-1]
        if shares > 0:
            sold_shares = shares
            notional = sold_shares * final_candle.close
            fee = notional * fee_rate
            cash += notional - fee
            shares = 0
            equity_curve[-1] = cash
            trades.append(
                BacktestTrade(
                    side='sell',
                    signal_timestamp=final_candle.timestamp,
                    execution_timestamp=final_candle.timestamp,
                    price=round(final_candle.close, 4),
                    shares=round(sold_shares, 6),
                    fee=round(fee, 4),
                    reason='end_of_period_liquidation',
                )
            )

        final_value = cash
        total_return = ((final_value / request.initial_capital) - 1) * 100
        benchmark_entry_price = ordered[request.slow_window].open
        benchmark_return = ((final_candle.close / benchmark_entry_price) - 1) * 100

        peak = equity_curve[0]
        max_drawdown = 0.0
        for equity in equity_curve:
            peak = max(peak, equity)
            drawdown = ((peak - equity) / peak) * 100 if peak else 0
            max_drawdown = max(max_drawdown, drawdown)

        return BacktestResponse(
            ticker=request.ticker,
            strategy=self.strategy_name,
            started_at=ordered[0].timestamp,
            ended_at=final_candle.timestamp,
            initial_capital=round(request.initial_capital, 2),
            final_value=round(final_value, 2),
            total_return_percent=round(total_return, 2),
            benchmark_return_percent=round(benchmark_return, 2),
            max_drawdown_percent=round(max_drawdown, 2),
            trade_count=sum(trade.side == 'sell' for trade in trades),
            trades=trades,
            parameters={
                'days': request.days,
                'fast_window': request.fast_window,
                'slow_window': request.slow_window,
                'fee_bps': request.fee_bps,
            },
        )
