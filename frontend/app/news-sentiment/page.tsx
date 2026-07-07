import Link from 'next/link';
import { apiGet } from '../../lib/api';
import { ErrorState } from '../../components/ErrorState';

export const dynamic = 'force-dynamic';

type NewsArticle = {
  ticker: string;
  title: string;
  source: string;
  url: string;
  published_at: string;
  sentiment: 'positive' | 'neutral' | 'negative';
  sentiment_score: number;
};

type NewsSentimentItem = {
  ticker: string;
  average_sentiment_score: number;
  sentiment: 'positive' | 'neutral' | 'negative';
  article_count: number;
  articles: NewsArticle[];
};

function sentimentLabel(score: number) {
  return score > 0 ? `+${score.toFixed(2)}` : score.toFixed(2);
}

export default async function Page() {
  let items: NewsSentimentItem[];
  try {
    items = await apiGet<NewsSentimentItem[]>('/news/sentiment');
  } catch (error) {
    return <ErrorState title="News sentiment unavailable" error={error} />;
  }

  return (
    <>
      <section className="card">
        <h2>News Sentiment</h2>
        <p>Mock provider sentiment across the tracked mega-cap universe.</p>
      </section>
      <section className="grid">
        {items.map(item => (
          <div className="card" key={item.ticker}>
            <p className="badge">{item.sentiment}</p>
            <h2><Link href={`/stock/${encodeURIComponent(item.ticker)}`}>{item.ticker}</Link></h2>
            <p>Average score: {sentimentLabel(item.average_sentiment_score)}</p>
            <p>Articles: {item.article_count}</p>
            <div className="table">
              {item.articles.map(article => (
                <div className="news-item" key={`${article.ticker}-${article.title}`}>
                  <p>{article.title}</p>
                  <small>{article.source} / {article.sentiment} / {sentimentLabel(article.sentiment_score)}</small>
                </div>
              ))}
            </div>
          </div>
        ))}
      </section>
    </>
  );
}
