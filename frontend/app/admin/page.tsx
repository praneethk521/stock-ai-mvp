import Link from 'next/link';
import { apiGet } from '../../lib/api';
import { ErrorState } from '../../components/ErrorState';

export const dynamic = 'force-dynamic';

type AdminStatus = {
  app_env: string;
  market_data_provider: string;
  news_provider: string;
  market_provider_health: { ok: boolean; provider: string; market?: string; mode?: string; error?: string };
  news_provider_health: { ok: boolean; provider: string; market?: string; mode?: string; error?: string };
  recommendation_model: string;
  persisted_recommendations: number;
  disclaimer: string;
};

type RecommendationHistoryItem = {
  id: number;
  ticker: string;
  recommendation: string;
  trade_horizon: string;
  confidence_score: number;
  risk_score: number;
  generated_at: string;
  model_version: string;
};

export default async function Page() {
  let status: AdminStatus;
  let recent: RecommendationHistoryItem[];
  try {
    [status, recent] = await Promise.all([
      apiGet<AdminStatus>('/admin/status'),
      apiGet<RecommendationHistoryItem[]>('/recommendations/recent?limit=5'),
    ]);
  } catch (error) {
    return <ErrorState title="Admin status unavailable" error={error} />;
  }

  return (
    <>
      <section className="grid">
        <div className="card">
          <h2>System Status</h2>
          <p>Environment: {status.app_env}</p>
          <p>Market provider: {status.market_data_provider}</p>
          <p>News provider: {status.news_provider}</p>
          <p>Market health: {status.market_provider_health.ok ? 'ok' : 'error'}</p>
          {status.market_provider_health.error ? <small>{status.market_provider_health.error}</small> : null}
          <p>News health: {status.news_provider_health.ok ? 'ok' : 'error'}</p>
          {status.news_provider_health.error ? <small>{status.news_provider_health.error}</small> : null}
          <p>Recommendation model: {status.recommendation_model}</p>
        </div>
        <div className="card">
          <h2>Persistence</h2>
          <p>Stored recommendations: {status.persisted_recommendations}</p>
          <p>{status.disclaimer}</p>
        </div>
      </section>
      <section className="card">
        <h2>Recent Recommendations</h2>
        {recent.length === 0 ? (
          <p>No recommendations generated yet.</p>
        ) : (
          <div className="table">
            {recent.map(item => (
              <div className="row" key={item.id}>
                <Link href={`/stock/${encodeURIComponent(item.ticker)}`}>{item.ticker}</Link>
                <span>{item.recommendation}</span>
                <span>{item.confidence_score.toFixed(1)}% confidence</span>
                <span>{new Date(item.generated_at).toLocaleString()}</span>
              </div>
            ))}
          </div>
        )}
      </section>
    </>
  );
}
