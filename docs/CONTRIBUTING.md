# Contributing

## Development Rules
- Keep MVP scope small
- Add tests for service logic
- Never commit secrets
- Update `docs/STATUS.md` after each meaningful change
- Update `docs/MILESTONES.md` when tasks complete

## Backend
Run:
```bash
cd backend
python -m ruff check app tests
python -m pytest
```

## Frontend
Run:
```bash
cd frontend
corepack enable
pnpm install --frozen-lockfile
pnpm run lint
pnpm run build
```
