# Architecture

## Overview

config-forge is split into two deployable units:

1. FastAPI backend that owns persistence, policy validation, and promotion workflows.
2. React dashboard that enables operators to submit, validate, and promote configs.

## Backend

- API Layer: FastAPI routes in `backend/app/main.py`.
- Domain Layer: validation and promotion logic in `backend/app/service.py`.
- Persistence Layer: SQLite data access in `backend/app/store.py`.
- Runtime Guards:
  - Allowed-host filtering
  - Payload-size limits
  - Security headers

## Frontend

- App shell in `frontend/src/App.tsx`.
- API client in `frontend/src/lib/api.ts`.
- Reusable UI atoms in `frontend/src/components`.

## Data Model

- `configs`: versioned configuration entities and status.
- `validations`: policy results and issue lists.
- `releases`: immutable promotion/audit records.

## Deployment

- Local and production compose files at repo root.
- CI, release, and pages workflows in `.github/workflows`.
- Container artifacts published to GHCR on tag push.
