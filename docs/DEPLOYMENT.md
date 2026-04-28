# Deployment

## Local

1. Copy `.env.example` to `.env`.
2. Run:

```bash
docker compose --env-file .env -f docker-compose.yml up --build
```

Backend: `http://localhost:8040`
Frontend: `http://localhost:8120`

## Production Compose

```bash
docker compose --env-file .env -f docker-compose.prod.yml up --build -d
```

## GitHub Actions

- `ci.yml`: backend tests, frontend build, compose validation.
- `release.yml`: publishes backend and frontend images to GHCR on tags.
- `pages.yml`: deploys frontend static build to GitHub Pages.
