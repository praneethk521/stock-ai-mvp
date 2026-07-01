import { apiGet } from '../../../lib/api';

export const dynamic = 'force-dynamic';

type Rec = { ticker: string; recommendation: string; trade_horizon: string; confidence_score: number; risk_score: number; explanation: string; supporting_signals: Record<string, unknown>; disclaimer: string };

export default async function StockPage({ params }: { params: Promise<{ ticker: string }> }) {
  const { ticker } = await params;
  const rec = await apiGet<Rec>(`/stocks/${ticker}/recommendation`);
  return <section className="card"><h2>{rec.ticker} Recommendation</h2><p><strong>{rec.recommendation}</strong> / {rec.trade_horizon}</p><p>Confidence: {rec.confidence_score}%</p><p>Risk: {rec.risk_score}%</p><p>{rec.explanation}</p><pre>{JSON.stringify(rec.supporting_signals, null, 2)}</pre><small>{rec.disclaimer}</small></section>;
}
