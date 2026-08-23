# Backtesting

Backtesting v1 provides a deterministic long-only SMA crossover simulation over historical candles from the configured market provider.

## Methodology

- The fast and slow simple moving averages use closing prices available at the end of each candle.
- A signal executes at the next candle's open, preventing same-candle look-ahead.
- The strategy invests all available capital on an entry and closes the full position on an exit.
- Configurable transaction fees apply to both buys and sells. Slippage, taxes, dividends, splits, and partial fills are not modeled.
- Any open position is liquidated at the final close.
- Buy-and-hold performance begins at the first executable candle after the SMA warm-up, matching the strategy's tradable interval.
- Maximum drawdown is calculated from the marked-to-market daily equity curve.

## API

`POST /api/v1/backtests` accepts a ticker, 20 to 365 calendar days, starting capital, fast/slow windows, and a fee in basis points. The fast window must be smaller than the slow window, and the requested history must exceed the slow window.

The response includes strategy and benchmark returns, final value, maximum drawdown, completed trade count, and an order ledger containing separate signal and execution timestamps.

## Scope

This is a research tool, not execution advice. The initial engine is intentionally reproducible and does not optimize parameters. Production expansion should add persisted runs, walk-forward testing, split/dividend-adjusted data validation, slippage models, parameter-sweep controls, and benchmark/evaluation datasets before strategy claims are made.
