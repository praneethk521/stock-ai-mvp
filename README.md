# Stock AI MVP

Production-minded stock market insights application for market movers, news sentiment, watchlists, and rules-based recommendations.

> Disclaimer: This app is informational only and is not financial advice.

## Stack
- Frontend: Next.js / React / TypeScript
- Backend: FastAPI / Python
- Database: PostgreSQL
- Cache: Redis
- Local runtime: Docker Compose
- Agent-ready layer: provider interfaces + agent/tool stubs

## Provider mode
The local demo defaults to mock providers. To use Polygon-backed market/news data, set:

```bash
MARKET_DATA_PROVIDER=polygon
NEWS_PROVIDER=polygon
POLYGON_API_KEY=your_polygon_key
```

Keep API keys in local `.env` files or a secret manager. Do not commit real keys.

## Run locally
```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
docker compose up --build
```

Open:
- Frontend: http://localhost:3000
- Backend docs: http://localhost:8000/docs

## Run local demo without Docker
Terminal 1:
```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
cd backend
../.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Terminal 2:
```bash
cd frontend
corepack enable
pnpm install
pnpm run dev
```

Open http://localhost:3000.

## Current scope
- Mock market overview
- Mock large-cap movers with configurable minimum market cap
- Mock ticker news
- Initial recommendation engine
- Persisted recommendation records
- Persisted watchlist
- Polygon provider adapter foundation
- Codex-friendly docs/status

## Next implementation steps
Follow `docs/MILESTONES.md` and update `docs/STATUS.md` after each completed task.
