import { revalidatePath } from 'next/cache';
import Link from 'next/link';
import { ErrorState } from '../../components/ErrorState';
import { apiGet, apiSend } from '../../lib/api';

export const dynamic = 'force-dynamic';

type PriceAlert = {
  id: number;
  ticker: string;
  condition: 'above' | 'below';
  target_price: number;
  is_active: boolean;
  last_price: number | null;
  triggered_at: string | null;
  created_at: string;
};

async function createAlert(formData: FormData) {
  'use server';
  const ticker = String(formData.get('ticker') ?? '').trim();
  const condition = String(formData.get('condition') ?? 'above');
  const targetPrice = Number(formData.get('target_price'));
  if (!ticker || !['above', 'below'].includes(condition) || !Number.isFinite(targetPrice) || targetPrice <= 0) return;
  await apiSend<PriceAlert>('/alerts', {
    method: 'POST',
    body: JSON.stringify({ ticker, condition, target_price: targetPrice }),
  });
  revalidatePath('/alerts');
}

async function evaluateAlerts() {
  'use server';
  await apiSend<PriceAlert[]>('/alerts/evaluate', { method: 'POST' });
  revalidatePath('/alerts');
}

async function deleteAlert(formData: FormData) {
  'use server';
  const id = Number(formData.get('id'));
  if (!Number.isInteger(id) || id <= 0) return;
  await apiSend<{ deleted: boolean; id: number }>(`/alerts/${id}`, { method: 'DELETE' });
  revalidatePath('/alerts');
}

async function rearmAlert(formData: FormData) {
  'use server';
  const id = Number(formData.get('id'));
  if (!Number.isInteger(id) || id <= 0) return;
  await apiSend<PriceAlert>(`/alerts/${id}`, {
    method: 'PUT',
    body: JSON.stringify({ is_active: true }),
  });
  revalidatePath('/alerts');
}

export default async function Page() {
  let alerts: PriceAlert[];
  try {
    alerts = await apiGet<PriceAlert[]>('/alerts');
  } catch (error) {
    return <ErrorState title="Price alerts unavailable" error={error} />;
  }

  const activeCount = alerts.filter(alert => alert.is_active).length;

  return (
    <>
      <section className="card">
        <div className="section-heading">
          <div>
            <h2>Price Alerts</h2>
            <p>{activeCount} active / {alerts.length} total</p>
          </div>
          <form action={evaluateAlerts}>
            <button type="submit">Check prices</button>
          </form>
        </div>
        <form action={createAlert} className="alert-form">
          <label>
            Ticker
            <input name="ticker" placeholder="NVDA" maxLength={12} required />
          </label>
          <label>
            Condition
            <select name="condition" defaultValue="above">
              <option value="above">At or above</option>
              <option value="below">At or below</option>
            </select>
          </label>
          <label>
            Target price
            <input name="target_price" type="number" min="0.01" max="1000000000" step="0.01" placeholder="210.00" required />
          </label>
          <button type="submit">Create alert</button>
        </form>
      </section>
      <section className="card">
        <div className="alert-row alert-header">
          <span>Ticker</span>
          <span>Threshold</span>
          <span>Last price</span>
          <span>Status</span>
          <span>Created</span>
          <span aria-label="Actions" />
        </div>
        {alerts.length === 0 ? (
          <p>No price alerts yet.</p>
        ) : alerts.map(alert => (
          <div className="alert-row" key={alert.id}>
            <strong><Link href={`/stock/${encodeURIComponent(alert.ticker)}`}>{alert.ticker}</Link></strong>
            <span>{alert.condition === 'above' ? 'At or above' : 'At or below'} ${alert.target_price.toFixed(2)}</span>
            <span>{alert.last_price === null ? 'Not checked' : `$${alert.last_price.toFixed(2)}`}</span>
            <span className="badge">{alert.is_active ? 'Active' : `Triggered${alert.triggered_at ? ` ${new Date(alert.triggered_at).toLocaleString()}` : ''}`}</span>
            <span>{new Date(alert.created_at).toLocaleDateString()}</span>
            <div className="alert-actions">
              {!alert.is_active ? (
                <form action={rearmAlert}>
                  <input type="hidden" name="id" value={alert.id} />
                  <button type="submit">Re-arm</button>
                </form>
              ) : null}
              <form action={deleteAlert}>
                <input type="hidden" name="id" value={alert.id} />
                <button type="submit">Delete</button>
              </form>
            </div>
          </div>
        ))}
      </section>
    </>
  );
}
