import { revalidatePath } from 'next/cache';
import Link from 'next/link';
import { apiGet, apiSend } from '../../lib/api';
import { ErrorState } from '../../components/ErrorState';

export const dynamic = 'force-dynamic';

type WatchlistItem = {
  id: number;
  ticker: string;
  notes: string;
  created_at: string;
};

async function addToWatchlist(formData: FormData) {
  'use server';
  const ticker = String(formData.get('ticker') ?? '').trim();
  const notes = String(formData.get('notes') ?? '').trim();
  if (!ticker) return;
  await apiSend<WatchlistItem>('/watchlist', {
    method: 'POST',
    body: JSON.stringify({ ticker, notes }),
  });
  revalidatePath('/watchlist');
}

async function removeFromWatchlist(formData: FormData) {
  'use server';
  const ticker = String(formData.get('ticker') ?? '').trim();
  if (!ticker) return;
  await apiSend<{ deleted: boolean; ticker: string }>(`/watchlist/${encodeURIComponent(ticker)}`, {
    method: 'DELETE',
  });
  revalidatePath('/watchlist');
}

export default async function Page() {
  let items: WatchlistItem[];
  try {
    items = await apiGet<WatchlistItem[]>('/watchlist');
  } catch (error) {
    return <ErrorState title="Watchlist unavailable" error={error} />;
  }

  return (
    <>
      <section className="card">
        <h2>Watchlist</h2>
        <form action={addToWatchlist} className="form">
          <label>
            Ticker
            <input name="ticker" placeholder="NVDA" maxLength={12} required />
          </label>
          <label>
            Notes
            <input name="notes" placeholder="Reason for watching" maxLength={500} />
          </label>
          <button type="submit">Add ticker</button>
        </form>
      </section>
      <section className="grid">
        {items.length === 0 ? (
          <div className="card"><p>No watchlist tickers yet.</p></div>
        ) : (
          items.map(item => (
            <div className="card" key={item.id}>
              <p className="badge">Watching</p>
              <h2><Link href={`/stock/${encodeURIComponent(item.ticker)}`}>{item.ticker}</Link></h2>
              <p>{item.notes || 'No notes yet.'}</p>
              <p>Added: {new Date(item.created_at).toLocaleString()}</p>
              <form action={removeFromWatchlist}>
                <input type="hidden" name="ticker" value={item.ticker} />
                <button type="submit">Remove</button>
              </form>
            </div>
          ))
        )}
      </section>
    </>
  );
}
