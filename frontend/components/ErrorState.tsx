import { apiErrorMessage } from '../lib/api';

export function ErrorState({ title, error }: { title: string; error: unknown }) {
  const details = apiErrorMessage(error);
  return (
    <section className="card error-card">
      <p className="badge">Unavailable</p>
      <h2>{title}</h2>
      <p>{details.message}</p>
      <small>{details.title}{details.requestId ? ` / request ${details.requestId}` : ''}</small>
    </section>
  );
}
