# Operations

## Runtime Safety

- Restrict allowed hosts with `CONFIG_FORGE_ALLOWED_HOSTS`.
- Restrict payload size with `CONFIG_FORGE_MAX_PAYLOAD_BYTES`.
- Enable HSTS in HTTPS environments with `CONFIG_FORGE_ENABLE_HSTS=true`.

## Promotion Workflow

1. Create config as `draft`.
2. Run validation.
3. Resolve issues if rejected.
4. Promote with change ticket and approver metadata.

## Backup

The SQLite DB lives at `CONFIG_FORGE_DB_PATH` and should be snapshot-backed in production.
