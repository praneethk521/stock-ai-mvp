import Link from 'next/link';

const links = [
  ['Dashboard', '/dashboard'],
  ['Large-Cap Movers', '/large-cap-movers'],
  ['News Sentiment', '/news-sentiment'],
  ['Recommendations', '/recommendations'],
  ['Watchlist', '/watchlist'],
  ['Admin', '/admin'],
];

export function Nav() {
  return <nav>{links.map(([label, href]) => <Link key={href} href={href}>{label}</Link>)}</nav>;
}
