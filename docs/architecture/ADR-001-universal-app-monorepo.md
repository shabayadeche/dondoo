# ADR-001 Universal App Monorepo

## Status

Superseded on August 19, 2026 by ADR-003.

## Decision

Use a monorepo with:

- one universal client app for web, iPhone, and Android,
- one clinical API service,
- one self-hosted Odoo layer for back-office and integration functions,
- shared packages for domain types, validation, and UI primitives.

## Selected Technology Direction

### Client

- Expo
- React Native
- Expo Router
- TypeScript

### API

- Node.js
- TypeScript
- PostgreSQL
- Prisma

### Back-Office Platform

- Self-hosted Odoo
- Custom Odoo modules
- Odoo security groups and record rules where applicable
- Odoo QWeb PDF and business workflow capabilities where appropriate

### Shared Packages

- `packages/domain`
- `packages/ui`
- `packages/config`

## Rationale

- One client codebase reduces divergence between web and mobile.
- The app is workflow and forms heavy, which suits a shared universal client.
- Shared validation and types reduce logic drift between client and server.
- A monorepo lowers coordination cost in a small product team.
- Odoo can handle admin, workflow, and business-facing features without forcing the clinical core into ERP-style UX.

## Consequences

### Positive

- Shared components and validation
- Easier feature parity between platforms
- One domain model and one task model
- Lower setup complexity than microservices
- Reuse of Odoo for users, tasks, document workflows, and admin processes

### Negative

- Requires discipline to avoid web-only or mobile-only assumptions
- PDF generation will likely remain server-side
- Some platform-specific UX branching is still required
- Integration boundaries between Odoo and the clinical API must stay explicit

## Rejected Alternatives

### Separate Web And Mobile Repositories

Rejected because:

- duplicate form logic,
- duplicate validation,
- higher maintenance cost,
- inconsistent rollout risk.

### Full EMR-Style Modular Platform In V1

Rejected because:

- scope too large,
- delays pilot validation,
- increases governance complexity before core workflow is proven.

### Odoo-Only Clinical Backend

Rejected because:

- the clinical procedure workflow needs tighter control over immutability, structured validation, and UX than Odoo should own alone,
- clinician-facing mobile and web interaction would be constrained by ERP-style patterns,
- long-term clinical reporting logic would become harder to evolve cleanly.
