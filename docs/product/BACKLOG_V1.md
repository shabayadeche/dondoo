# Backlog V1

## Status Snapshot As Of August 25, 2026

- Implemented in the repo: platform foundation, clinician PWA shell, FastAPI clinical service, database migrations, local and Odoo-backed authentication paths, draft save and resume, multi-procedure case workspace, report preview and PDF export, follow-up task flow, finalized lock and reopen flow, audit history, and acceptance tests.
- Remaining before production release: pilot usability fixes, mobile install validation, deployment and security hardening, and release acceptance checks.

## Milestone 1: Product And Architecture Baseline

- Approve PRD
- Approve data dictionary
- Approve screen-field map
- Approve roles and sign-off rules
- Approve schema and repo structure

## Milestone 2: Platform Foundation

- Set up monorepo
- Set up clinician PWA shell
- Set up FastAPI clinical service
- Set up PostgreSQL and migrations
- Set up authentication
- Set up role-based authorization
- Set up audit event infrastructure

## Milestone 3: Case And Shared Workflow

- Create patient search and patient entry flow
- Create new case flow
- Build shared header and safety steps
- Build draft save and resume behavior
- Build review step shell

## Milestone 4: Colonoscopy Module

- Build prep and completeness step
- Build segment exam step
- Build lesion log step
- Build resection and follow-up step
- Build impression and communication step

## Milestone 5: Reporting And Follow-Up

- Build narrative generation service
- Build PDF export
- Build specimen capture
- Build follow-up task creation
- Build follow-up task list and closure flow

## Milestone 6: Governance And Hardening

- Build finalized lock behavior
- Build reopen flow
- Build audit viewer
- Run pilot usability fixes
- Run release acceptance checks

## Suggested Priority Order

### P0

- auth
- authorization
- draft save
- colonoscopy form
- report generation
- final sign-off
- audit

### P1

- specimen follow-up
- task queue
- PDF polish
- mobile task views

### P2

- admin UX polish
- quality reviewer views
- post-pilot optimization
