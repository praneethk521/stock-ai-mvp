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
ruff check app tests
pytest
```

## Frontend
Run:
```bash
cd frontend
npm install
npm run build
```
