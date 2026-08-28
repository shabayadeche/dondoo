# Production Release Checklist

Use this checklist before the first production cutover and before every later release.

## Preflight

- Production host is patched and reachable over SSH.
- PostgreSQL is available and the target database exists.
- TLS certificate and key paths are present on the host.
- Public DNS points at the Nginx host.
- The deployment checkout matches the intended release state.

## Secrets And Config

- `/etc/phd-ass/clinical-api.env` exists and is based on [services/clinical_api/.env.production.example](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/services/clinical_api/.env.production.example).
- `CLINICAL_API_LOCAL_AUTH_PASSWORD` is not the development fallback.
- `ALLOW_ORIGINS` matches the public HTTPS frontend origin.
- `CLINICAL_API_TRUSTED_HOSTS` matches the public hostnames.
- `CLINICAL_API_REQUIRE_HTTPS=true`.
- `CLINICAL_API_ENABLE_DOCS=false`.
- `CLINICAL_API_SEED_SAMPLE_DATA=false`.
- Odoo bridge secrets are present only if Odoo is part of this rollout.

## Build And Runtime

- `npm run build:pwa` completed successfully.
- The published PWA assets came from the same release commit.
- The Python virtual environment is up to date for this release.
- `alembic upgrade head` succeeds on the target database.
- `sudo systemctl status phd-ass-clinical-api.service` is healthy after restart.
- `sudo nginx -t` succeeds before reloading Nginx.

## Smoke Tests

- Public `GET /health` returns `200`.
- Login succeeds with a valid clinician account.
- Repeated bad logins trigger API throttling.
- Draft create and draft save succeed.
- Report preview and finalize succeed.
- Finalized PDF opens from the PWA.
- Reopen is blocked for non-admin roles.
- Reopen succeeds for `operations_admin` or `workspace_admin` with a reason.
- Follow-up task closure requires a resolution note.

## Mobile Acceptance

- iPhone Safari install flow works over HTTPS.
- Android Chrome install flow works over HTTPS.
- Login works on both mobile platforms.
- Draft save works on both mobile platforms.
- Finalize works on both mobile platforms for an `endoscopist`.
- PDF open works on both mobile platforms.

## Operational Readiness

- Previous PWA release artifacts are still available for rollback.
- The previous API environment file is still recoverable.
- Journald or external log collection is enabled for the clinical API service.
- Support owners know the rollback steps and restart commands.
