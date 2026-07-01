import './globals.css';
import { Nav } from '../components/Nav';

export const metadata = { title: 'Stock AI MVP', description: 'Informational stock analysis, not financial advice.' };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body><main><h1>Stock AI MVP</h1><p className="badge">Informational only. Not financial advice.</p><Nav />{children}</main></body></html>;
}
