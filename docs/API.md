# API

Base URL: `http://localhost:8040`

## Health

- `GET /healthz`
- `GET /readyz`

## Configs

- `POST /api/v1/configs`
  - Creates a new versioned config.
- `GET /api/v1/configs`
  - Returns all configs sorted by newest first.

## Validation

- `POST /api/v1/configs/{config_id}/validate`
  - Evaluates required/forbidden keys and numeric guardrails.
- `GET /api/v1/configs/{config_id}/validation`
  - Returns latest validation result.

## Promotion

- `POST /api/v1/configs/{config_id}/promote`
  - Requires passed validation.
  - Creates an immutable release event.

## Releases

- `GET /api/v1/releases`
  - Lists rollout records for audit.
