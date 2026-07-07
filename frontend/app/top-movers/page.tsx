import Link from 'next/link';
import { apiGet } from '../../lib/api';

export const dynamic = 'force-dynamic';

type Mover = { ticker: string; company_name: string; price: number; change_percent: number; volume: number; market_cap: number };

function money(value: number) {
  if (!value) return 'n/a';
  if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  return `$${value.toLocaleString()}`;
}

async function getMovers(direction: 'gainers' | 'losers') {
  return apiGet<{ direction: string; items: Mover[] }>(`/market/top-movers?direction=${direction}&limit=10`);
}

export default async function TopMovers() {
  const [gainers, losers] = await Promise.all([getMovers('gainers'), getMovers('losers')]);

  return (
    <>
      <section className="card">
        <h2>Top Market Movers</h2>
        <p>All-market gainers and losers from the active provider. Local mock mode uses the tracked mega-cap demo universe.</p>
      </section>
      <section className="grid">
        <MoverColumn title="Top Gainers" items={gainers.items} />
        <MoverColumn title="Top Losers" items={losers.items} />
      </section>
    </>
  );
}

function MoverColumn({ title, items }: { title: string; items: Mover[] }) {
  return (
    <div className="card">
      <h2>{title}</h2>
      <div className="table">
        {items.map((m, index) => (
          <div className="mover-row" key={m.ticker}>
            <p className="badge">#{index + 1}</p>
            <div>
              <h3><Link href={`/stock/${encodeURIComponent(m.ticker)}`}>{m.ticker}</Link></h3>
              <p>{m.company_name}</p>
            </div>
            <div>
              <p>${m.price.toFixed(2)}</p>
              <small>{m.change_percent.toFixed(2)}%</small>
            </div>
            <div>
              <p>{m.volume.toLocaleString()}</p>
              <small>{money(m.market_cap)}</small>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
