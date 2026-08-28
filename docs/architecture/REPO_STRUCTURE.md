# Repo Structure

## Repo Layout

```text
PhD-Ass/
  apps/
    pwa/
    app/  # legacy Expo reference
  deploy/
    nginx/
    systemd/
  services/
    clinical_api/
    api/  # legacy Fastify reference
    odoo_addons/
  packages/
    domain/
    ui/
    config/
  docs/
    architecture/
    operations/
    product/
  stakeholder-approval/
```

## Purpose Of Each Area

### apps/pwa

Clinician-facing progressive web app targeting:

- desktop browsers
- tablets
- iPhone home-screen install
- Android home-screen install

### apps/app

Legacy Expo reference retained while cleanup and retirement work is completed.

### services/clinical_api

Python FastAPI service responsible for:

- authentication hooks
- authorization
- report generation
- PDF generation
- follow-up tasks
- database access
- audit events
- Odoo bridge endpoints

### services/api

Legacy Fastify reference retained while cleanup and retirement work is completed.

### services/odoo_addons

Custom Odoo modules responsible for:

- user and role alignment
- back-office workflow configuration
- document/admin process support
- integration endpoints into the clinical service where needed

### deploy

Deployment scaffolding for:

- reverse-proxy examples
- service-manager examples
- production host bootstrap references

### packages/domain

Shared source of truth for:

- TypeScript domain types
- validation schemas
- enums
- shared workflow constants

### packages/ui

Shared UI primitives and design-system components.

### packages/config

Shared linting, TypeScript, and tooling presets if needed.

## Cleanup Sequence

1. Keep `apps/pwa` and `services/clinical_api` as the active clinician stack.
2. Retire `apps/app` after any remaining reference shapes are migrated or deleted.
3. Retire `services/api` after any remaining historical Prisma or TypeScript shapes are migrated or deleted.
4. Preserve shared domain and UI packages only where they still serve the active stack.

## Constraints

- Do not put domain validation only in the frontend.
- Do not put generated report rules only in the UI.
- Keep procedure-specific modules isolated so EGD, ERCP, and EUS can be added later without destabilizing colonoscopy.
- Do not move the clinical reporting core into Odoo models unless a later decision explicitly changes the architecture.
