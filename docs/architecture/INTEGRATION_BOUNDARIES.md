# Integration Boundaries

## Purpose

Define which system owns which responsibility in the self-hosted hybrid architecture.

## System Split

### Universal App

Owns:

- clinician-facing web UX
- clinician-facing mobile UX
- workflow navigation
- validation feedback
- report preview
- task review UI

Does not own:

- persistence rules
- final audit storage
- sign-off authority checks

### Clinical API

Owns:

- case CRUD rules
- structured validation
- case state machine
- report generation
- final sign-off
- reopen logic
- audit events
- clinical follow-up tasks

Does not own:

- ERP or business admin workflows
- generic business approvals outside clinical scope

### PostgreSQL

Owns:

- clinical source of truth
- structured procedure data
- finalized snapshots
- audit events

### Odoo

Owns:

- self-hosted back-office capabilities
- optional identity source
- configurable admin processes
- optional non-clinical approvals
- optional cross-system integration utilities

Does not own in V1:

- procedure workflow state machine
- final clinical note generation rules
- locked finalized record logic

## Recommended Early Integration Scope

### Phase 1

- no deep real-time integration required
- Odoo can remain administratively adjacent while the clinical core is built

### Phase 2

- user synchronization
- task or notification synchronization if useful
- report archive or document handoff if required

### Phase 3

- broader administrative workflow integration
- patient master sync if stakeholders approve it

## Identity Recommendation

Recommended V1:

- keep authentication strategy simple,
- let the clinical app manage its own session/auth layer,
- optionally mirror users from Odoo later,
- avoid coupling first release login flow tightly to Odoo unless the team already runs Odoo identity confidently.

## Reporting Recommendation

Recommended V1:

- generate final clinical PDFs from the clinical service,
- optionally push copies or metadata into Odoo later,
- do not make Odoo the canonical final report renderer for V1.

## Task Recommendation

Recommended V1:

- keep clinical follow-up tasks in the clinical service because they depend on case context and audit rules,
- optionally sync summary task states to Odoo for admin visibility later.
