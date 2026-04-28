# Contributing

## Development Setup

1. Copy `.env.example` to `.env`.
2. Backend:
   - `cd backend`
   - `python -m venv .venv`
   - `.\\.venv\\Scripts\\Activate.ps1`
   - `pip install -r requirements.txt`
   - `pytest -q`
3. Frontend:
   - `cd frontend`
   - `npm install`
   - `npm run build`

## Pull Request Rules

- Keep changes scoped to a single concern.
- Update docs if API or behavior changes.
- Ensure CI checks pass before requesting review.
