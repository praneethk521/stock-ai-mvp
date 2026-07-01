import { apiGet } from '../../lib/api';

export const dynamic = 'force-dynamic';

type Overview = { indices: { symbol: string; change_percent: number }[]; disclaimer: string };

export default async function Dashboard() {
  const overview = await apiGet<Overview>('/market/overview');
  return <section className="grid"><div className="card"><h2>Market Overview</h2>{overview.indices.map(i => <p key={i.symbol}>{i.symbol}: {i.change_percent}%</p>)}<small>{overview.disclaimer}</small></div></section>;
}
