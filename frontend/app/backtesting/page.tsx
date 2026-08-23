import Link from 'next/link';
import { ErrorState } from '../../components/ErrorState';
import { apiSend } from '../../lib/api';

export const dynamic = 'force-dynamic';

type BacktestTrade = {
  side: 'buy' | 'sell';
  signal_timestamp: string;
  execution_timestamp: string;
  price: number;
  shares: number;
  fee: number;
  reason: string;
};

type BacktestResult = {
  ticker: string;
  strategy: string;
  started_at: string;
  ended_at: string;
  initial_capital: number;
  final_value: number;
  total_return_percent: number;
  benchmark_return_percent: number;
  max_drawdown_percent: number;
  trade_count: number;
  trades: BacktestTrade[];
  parameters: Record<string, number>;
  disclaimer: string;
};

type PageProps = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

function valueOf(value: string | string[] | undefined, fallback: string) {
  return typeof value === 'string' ? value : fallback;
}

export default async function Page({ searchParams }: PageProps) {
  const query = await searchParams;
  const ticker = valueOf(query.ticker, 'NVDA').trim().toUpperCase();
  const days = Number(valueOf(query.days, '180'));
  const fastWindow = Number(valueOf(query.fast_window, '10'));
  const slowWindow = Number(valueOf(query.slow_window, '30'));
  const feeBps = Number(valueOf(query.fee_bps, '5'));
  const shouldRun = query.run === 'true';
  let result: BacktestResult | null = null;
  let error: unknown = null;

  if (shouldRun) {
    try {
      result = await apiSend<BacktestResult>('/backtests', {
        method: 'POST',
        body: JSON.stringify({
          ticker,
          days,
          fast_window: fastWindow,
          slow_window: slowWindow,
          fee_bps: feeBps,
          initial_capital: 10_000,
        }),
      });
    } catch (caught) {
      error = caught;
    }
  }

  return (
    <>
      <section className="card">
        <h2>Strategy Backtest</h2>
        <form method="get" className="backtest-form">
          <input type="hidden" name="run" value="true" />
          <label>Ticker<input name="ticker" defaultValue={ticker} maxLength={12} required /></label>
          <label>History (days)<input name="days" type="number" defaultValue={days} min="20" max="365" required /></label>
          <label>Fast SMA<input name="fast_window" type="number" defaultValue={fastWindow} min="2" max="100" required /></label>
          <label>Slow SMA<input name="slow_window" type="number" defaultValue={slowWindow} min="3" max="200" required /></label>
          <label>Fee (bps)<input name="fee_bps" type="number" defaultValue={feeBps} min="0" max="100" step="0.1" required /></label>
          <button type="submit">Run backtest</button>
        </form>
      </section>

      {error ? <ErrorState title="Backtest unavailable" error={error} /> : null}

      {result ? (
        <>
          <section className="metric-grid">
            <div><small>Strategy return</small><strong>{result.total_return_percent.toFixed(2)}%</strong></div>
            <div><small>Buy and hold</small><strong>{result.benchmark_return_percent.toFixed(2)}%</strong></div>
            <div><small>Maximum drawdown</small><strong>{result.max_drawdown_percent.toFixed(2)}%</strong></div>
            <div><small>Final value</small><strong>${result.final_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}</strong></div>
          </section>
          <section className="card">
            <div className="section-heading">
              <div>
                <p className="badge">{result.strategy}</p>
                <h2><Link href={`/stock/${encodeURIComponent(result.ticker)}`}>{result.ticker}</Link></h2>
              </div>
              <p>{new Date(result.started_at).toLocaleDateString()} to {new Date(result.ended_at).toLocaleDateString()}</p>
            </div>
            <p>{result.trade_count} completed trade{result.trade_count === 1 ? '' : 's'} / ${result.initial_capital.toLocaleString()} starting capital</p>
            <small>{result.disclaimer}</small>
          </section>
          <section className="card">
            <h2>Executed Orders</h2>
            {result.trades.length === 0 ? <p>No signals executed in this period.</p> : (
              <div className="table">
                <div className="backtest-row backtest-header"><span>Side</span><span>Execution</span><span>Price</span><span>Shares</span><span>Fee</span><span>Reason</span></div>
                {result.trades.map((trade, index) => (
                  <div className="backtest-row" key={`${trade.execution_timestamp}-${trade.side}-${index}`}>
                    <strong>{trade.side.toUpperCase()}</strong>
                    <span>{new Date(trade.execution_timestamp).toLocaleDateString()}</span>
                    <span>${trade.price.toFixed(2)}</span>
                    <span>{trade.shares.toFixed(4)}</span>
                    <span>${trade.fee.toFixed(2)}</span>
                    <span>{trade.reason.replaceAll('_', ' ')}</span>
                  </div>
                ))}
              </div>
            )}
          </section>
        </>
      ) : null}
    </>
  );
}
