# Clinical API

Python FastAPI service for the canonical clinical workflow.

## Current Backend Mode

As of August 25, 2026:

- local standalone mode is database-backed by default,
- Odoo is optional and can remain the identity and bridge layer when configured,
- case drafts, follow-up tasks, finalized revisions, PDFs, and audit events persist in the clinical API database,
- the legacy `services/api` Fastify scaffold is reference-only.

The clinical API now exposes:

- `GET /api/cases`
- `GET /api/cases/{external_case_id}`
- `GET /api/cases/{external_case_id}/history`
- `GET /api/cases/{external_case_id}/pdf`
- `GET /api/cases/{external_case_id}/revisions/{revision_number}/pdf`
- `PUT /api/cases/{external_case_id}`
- `POST /api/cases`
- `POST /api/cases/{external_case_id}/actions/{action}`
- `GET /api/tasks`
- `PUT /api/tasks/{external_task_id}`
- `GET /api/lookups`
- `POST /api/session/login`
- `GET /api/session/me`
- `POST /api/session/logout`

## Local Authentication

If the Odoo bridge is not configured, the service uses local workspace logins.

Defaults:

- users come from the seeded workspace profile list in [app/reference_data.py](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/services/clinical_api/app/reference_data.py)
- the shared local password comes from `CLINICAL_API_LOCAL_AUTH_PASSWORD`
- the default local password in development is `phd-ass-demo`

When the Odoo bridge is configured, login continues through Odoo.

Configuration examples:

- local defaults: [services/clinical_api/.env.example](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/services/clinical_api/.env.example)
- production defaults: [services/clinical_api/.env.production.example](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/services/clinical_api/.env.production.example)

## Security Defaults

As of August 25, 2026, the clinical API now hardens the default runtime with:

- trusted-host filtering through `CLINICAL_API_TRUSTED_HOSTS`
- stricter CORS origin, method, and header allow-lists
- security response headers on `/health` and `/api/*`
- login throttling through `CLINICAL_API_LOGIN_MAX_ATTEMPTS` and `CLINICAL_API_LOGIN_WINDOW_SECONDS`
- active-session caps through `CLINICAL_API_MAX_ACTIVE_SESSIONS_PER_USER`
- production rejection of the development fallback password
- optional HTTPS enforcement with docs disabled by default outside development

Important settings:

- `CLINICAL_API_SESSION_TTL_MINUTES`
- `CLINICAL_API_ENABLE_DOCS`
- `CLINICAL_API_REQUIRE_HTTPS`
- `CLINICAL_API_TRUST_FORWARDED_PROTO`
- `CLINICAL_API_HSTS_MAX_AGE_SECONDS`

## Database And Migrations

Default local database URL:

- `DATABASE_URL=sqlite:///./clinical_api.db`

Production target:

- PostgreSQL through `DATABASE_URL`

Migration commands:

```powershell
npm run clinical:db:migrate
```

WSL launcher behavior:

- [scripts/wsl-start-clinical-api.sh](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/scripts/wsl-start-clinical-api.sh) now runs `alembic upgrade head` before Uvicorn starts.

## Local Development

Recommended from WSL:

```bash
cd /mnt/c/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/services/clinical_api
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Managed launcher from Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-clinical-api.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\stop-clinical-api.ps1
```

## Tests

Acceptance coverage lives in [tests/test_acceptance.py](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/services/clinical_api/tests/test_acceptance.py).

Install the test dependency and run the suite:

```bash
cd /mnt/c/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/services/clinical_api
source /home/shabaya/.venvs/phd-ass-clinical-api/bin/activate
pip install -e ".[test]"
export PYTHONPATH="$(pwd)"
python3 -m unittest discover -s tests -v
```

## Odoo Bridge

Bridge configuration example:

```bash
export ODOO_BRIDGE_BASE_URL=http://127.0.0.1:8069
export ODOO_BRIDGE_DB_NAME=replace-with-odoo-db-name
export ODOO_BRIDGE_API_KEY=replace-with-odoo-bridge-key
export ODOO_BRIDGE_TIMEOUT_SECONDS=10
```

When configured, the clinical API can:

- authenticate users through Odoo,
- mirror draft case payloads,
- pull case history from Odoo,
- proxy finalized PDFs and revision PDFs through the FastAPI surface.

## Production Readiness Notes

- Put the clinical API behind HTTPS before enabling the installable PWA for real users.
- Set `CLINICAL_API_LOCAL_AUTH_PASSWORD` to a non-default secret before any non-development deployment.
- Set `CLINICAL_API_TRUSTED_HOSTS` to the real frontend and API hostnames before exposing the service.
- Keep `allow_origins` limited to explicit HTTPS origins outside local development.
- Keep the Odoo bridge reachable only from the clinical API or an internal reverse proxy path.
- Keep Odoo asset downloads on the configured Odoo origin only.
- Route workflow transitions through the explicit case action endpoints so finalize, reopen, and audit logic stay authoritative.
- Route follow-up status changes through the dedicated task update endpoint so closure validation and audit metadata stay consistent.

Deployment scaffolding in this repo:

- runbook: [docs/operations/PRODUCTION_DEPLOYMENT.md](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/docs/operations/PRODUCTION_DEPLOYMENT.md)
- release checklist: [docs/operations/PRODUCTION_RELEASE_CHECKLIST.md](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/docs/operations/PRODUCTION_RELEASE_CHECKLIST.md)
- Nginx example: [deploy/nginx/phd-ass.conf.example](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/deploy/nginx/phd-ass.conf.example)
- systemd example: [deploy/systemd/phd-ass-clinical-api.service.example](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/deploy/systemd/phd-ass-clinical-api.service.example)
