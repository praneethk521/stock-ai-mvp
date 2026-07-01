import Link from 'next/link';
import { apiGet } from '../../lib/api';

export const dynamic = 'force-dynamic';

type Mover = { ticker: string; company_name: string; price: number; change_percent: number; volume: number; market_cap: number };

export default async function LargeCapMovers() {
  const data = await apiGet<{ items: Mover[] }>('/market/large-cap-movers?min_market_cap=50000000000');
  return <section className="grid">{data.items.map(m => <div className="card" key={m.ticker}><h2><Link href={`/stock/${m.ticker}`}>{m.ticker}</Link></h2><p>{m.company_name}</p><p>Price: ${m.price}</p><p>Change: {m.change_percent}%</p><p>Market cap: ${(m.market_cap / 1e9).toFixed(0)}B</p></div>)}</section>;
}
