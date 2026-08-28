# ADR-003 React PWA And FastAPI Direction

## Status

Accepted on August 19, 2026.

## Decision

Shift the target implementation direction to:

- one clinician-facing React progressive web app,
- one Python FastAPI clinical service,
- one self-hosted Odoo layer for operations, reference data, and bridge workflows,
- shared domain artifacts that can be consumed across frontend and backend boundaries.

Keep the existing `apps/app` Expo scaffold and `services/api` Fastify scaffold only as transitional references until the migration is complete.

## Selected Technology Direction

### Clinician Frontend

- React
- TypeScript
- installable PWA behavior
- responsive layouts for desktop, tablet, iPhone, and Android

### Clinical API

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy and Alembic

### Back-Office Platform

- Self-hosted Odoo
- custom Odoo modules
- bridge endpoints and mirror models

## Rationale

- A PWA fits the requirement for one deployable mobile-capable surface for both Android and iPhone users.
- Python reduces stack fragmentation because Odoo is already Python-based.
- FastAPI supports explicit schemas, validation, and clean clinical API boundaries without forcing the clinician workflow into Odoo.
- This keeps the app install-light for internal rollout while preserving a path to native wrappers later if mobile constraints demand it.

## Consequences

### Positive

- simpler backend language story
- installable mobile access without app-store dependency
- clearer separation between clinical API and Odoo operations layer
- easier reuse of Python-side validation and reporting services

### Negative

- the current Expo and Fastify scaffolds become transitional debt
- shared validation can no longer assume TypeScript-only ownership
- iPhone install and background behavior remain weaker than full native apps
- a deliberate migration path is needed for any code already built in the legacy scaffolds

## Required Follow-On Work

1. Create the clinician PWA in `apps/pwa`.
2. Move the canonical clinical API into `services/clinical_api`.
3. Decide whether shared schemas stay TypeScript-first, become language-neutral, or are duplicated intentionally with tests.
4. Retire `apps/app` and `services/api` once the replacement paths are live.
