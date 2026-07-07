import Link from 'next/link';
import { apiGet } from '../../lib/api';
import { ErrorState } from '../../components/ErrorState';

export const dynamic = 'force-dynamic';

type RecommendationHistoryItem = {
  id: number;
  ticker: string;
  recommendation: string;
  trade_horizon: string;
  confidence_score: number;
  risk_score: number;
  explanation: string;
  generated_at: string;
  model_version: string;
};

export default async function Page() {
  let recent: RecommendationHistoryItem[];
  try {
    recent = await apiGet<RecommendationHistoryItem[]>('/recommendations/recent?limit=20');
  } catch (error) {
    return <ErrorState title="Recommendation history unavailable" error={error} />;
  }

  return (
    <>
      <section className="card">
        <h2>Recent Recommendations</h2>
        <p>Persisted outputs from the rules-based recommendation engine.</p>
      </section>
      <section className="grid">
        {recent.length === 0 ? (
          <div className="card"><p>No recommendations generated yet.</p></div>
        ) : (
          recent.map(item => (
            <div className="card" key={item.id}>
              <p className="badge">{item.recommendation} / {item.trade_horizon}</p>
              <h2><Link href={`/stock/${encodeURIComponent(item.ticker)}`}>{item.ticker}</Link></h2>
              <p>Confidence: {item.confidence_score.toFixed(1)}%</p>
              <p>Risk: {item.risk_score.toFixed(1)}%</p>
              <p>Model: {item.model_version}</p>
              <p>{new Date(item.generated_at).toLocaleString()}</p>
              <p>{item.explanation}</p>
            </div>
          ))
        )}
      </section>
    </>
  );
}
