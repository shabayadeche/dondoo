# ADR-002 Self-Hosted Hybrid Odoo Architecture

## Status

Accepted as the preferred architecture direction on August 18, 2026.

## Decision

Use a hybrid self-hosted architecture:

- a custom universal clinical app for web, iPhone, and Android,
- a custom clinical API and PostgreSQL database for the procedure workflow,
- a self-hosted Odoo instance for back-office operations, workflow administration, and selected integration responsibilities.

## Core Principle

The clinical reporting engine remains outside Odoo.

Odoo supports the product, but does not own:

- procedure workflow state,
- final report immutability,
- clinical field validation,
- structured lesion/specimen logic,
- narrative report generation rules.

## Odoo Responsibilities

- user and role administration where desired
- internal operational tasks where appropriate
- configurable admin workflows
- business-facing approvals
- document workflow support
- future ERP-style extensions that are not part of the clinical core

## Clinical Service Responsibilities

- case lifecycle
- shared safety workflow
- colonoscopy workflow
- report generation
- final sign-off
- reopen controls
- audit events
- follow-up tasks linked to clinical context

## Why This Split

- Odoo is strong for administrative business workflows.
- The clinical workflow has stricter requirements around immutability, UX, and structured reporting.
- Self-hosting removes Odoo SaaS API plan constraints and gives full deployment control.
- The hybrid split preserves future flexibility: Odoo can expand without forcing the clinical app to become ERP-shaped.

## Data Ownership

### Odoo Owns

- Odoo users and groups if selected as identity source
- operational admin records added later
- optional non-clinical workflow data

### Clinical Service Owns

- procedure cases
- procedure field data
- finalized narrative snapshots
- clinical audit trail
- specimen records
- clinical follow-up tasks

## Integration Pattern

- Odoo and the clinical API communicate through explicit service boundaries.
- Do not couple the clinician PWA directly to Odoo business objects for clinical workflow screens.
- Prefer API-level synchronization or controlled webhook-style integration.

## Consequences

### Positive

- cleaner clinical domain boundaries
- stronger control over finalization and audit
- easier mobile/web UX tuning
- Odoo remains available for future admin automation

### Negative

- two backend surfaces to operate
- integration contracts must be maintained
- user and role synchronization needs discipline

## Decision Guardrails

- If a feature directly affects clinical reporting correctness, it belongs in the clinical service first.
- If a feature is primarily administrative, configurable, or ERP-like, Odoo is the first candidate.
- Do not let Odoo templates become the source of truth for finalized clinical report content in V1.
