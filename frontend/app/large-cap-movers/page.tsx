import Link from 'next/link';
import { apiGet } from '../../lib/api';

export const dynamic = 'force-dynamic';

type Mover = { ticker: string; company_name: string; price: number; change_percent: number; volume: number; market_cap: number };

export default async function LargeCapMovers() {
  const data = await apiGet<{ items: Mover[] }>('/market/large-cap-movers?min_market_cap=50000000000');
  return (
    <>
      <section className="card">
        <h2>Top Mega-Cap Movers</h2>
        <p>Top 10 tracked companies by market cap, ranked by absolute daily move. Mock data for local demo only.</p>
      </section>
      <section className="grid">
        {data.items.map((m, index) => {
          const direction = m.change_percent >= 0 ? 'Up' : 'Down';
          return (
            <div className="card" key={m.ticker}>
              <p className="badge">#{index + 1} {direction}</p>
              <h2><Link href={`/stock/${encodeURIComponent(m.ticker)}`}>{m.ticker}</Link></h2>
              <p>{m.company_name}</p>
              <p>Price: ${m.price.toFixed(2)}</p>
              <p>Move: {m.change_percent.toFixed(2)}%</p>
              <p>Volume: {m.volume.toLocaleString()}</p>
              <p>Market cap: ${(m.market_cap / 1e12).toFixed(2)}T</p>
            </div>
          );
        })}
      </section>
    </>
  );
}
