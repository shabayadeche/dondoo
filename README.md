# PhD-Ass

Hybrid self-hosted endoscopy reporting platform for structured endoscopy reporting, follow-up tracking, and auditable sign-off.

## Architecture

- Active clinician frontend: React PWA for desktop, tablet, iPhone, and Android home-screen install
- Active clinical backend: Python + FastAPI + PostgreSQL
- Back-office layer: self-hosted Odoo with custom addons
- Legacy references retained for cleanup: `apps/app` (Expo) and `services/api` (Fastify)
- Shared packages: domain, UI, config

## Start Points

- Build and product docs: [docs/README.md](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/docs/README.md)
- Operations runbook: [docs/operations/PRODUCTION_DEPLOYMENT.md](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/docs/operations/PRODUCTION_DEPLOYMENT.md)
- Odoo and app form ownership: [docs/architecture/ODOO_APP_FORM_OWNERSHIP.md](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/docs/architecture/ODOO_APP_FORM_OWNERSHIP.md)
- Stakeholder pack: [stakeholder-approval/endoscopy-app-approval-pack.pdf](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/stakeholder-approval/endoscopy-app-approval-pack.pdf)

## Current Scripts

- `npm run dev:pwa` for the clinician PWA
- `npm run dev:app` for the legacy Expo scaffold
- `npm run dev:api` for the legacy Fastify scaffold
- `npm run typecheck`
- `npm run db:generate`
- `npm run clinical:db:migrate`
- `npm run clinical:start`
- `npm run clinical:stop`
- `npm run odoo:start`
- `npm run odoo:stop`
- `npm run odoo:proxy:start`
- `npm run odoo:proxy:stop`
- `npm run stack:start`
- `npm run stack:stop`
- `npm run stack:status`

## Python Clinical API

Active clinical service:

- [services/clinical_api/README.md](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/services/clinical_api/README.md)

Legacy backend reference:

- [services/api/README.md](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/services/api/README.md)

Clinician PWA:

- [apps/pwa/README.md](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/apps/pwa/README.md)

## Local Odoo

- Odoo is installed in the default WSL distro `Ubuntu`
- Start the full local stack with `powershell -ExecutionPolicy Bypass -File .\scripts\start-local-stack.ps1`
- Stop the full local stack with `powershell -ExecutionPolicy Bypass -File .\scripts\stop-local-stack.ps1`
- Inspect service state with `powershell -ExecutionPolicy Bypass -File .\scripts\status-local-stack.ps1`
- On the current WSL setup, Odoo is directly reachable from Windows at `http://127.0.0.1:8069/web/login`
- If Windows localhost forwarding is unavailable on another machine, start the fallback relay with `npm run odoo:proxy:start`
- Stop the fallback relay with `npm run odoo:proxy:stop`
