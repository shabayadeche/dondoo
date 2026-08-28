# Odoo And App Form Ownership

## Purpose

Define how the same endoscopy form fields appear in both the clinician PWA and Odoo without creating two conflicting clinical systems.

## Decision Summary

- Every V1 field group should have a representation in both the clinician PWA and Odoo for visibility and operational continuity.
- Shared representation does not mean shared ownership.
- The clinical API and PostgreSQL remain the source of truth for all clinical case data, workflow state, validation, report generation, sign-off, and audit history.
- Odoo may mirror the same field groups, but it must not become a second clinical workflow engine.
- If Odoo needs editable clinical screens later, those screens must save through clinical API endpoints, not through independent Odoo-only logic.

## Product Rule

Use one shared field contract across both surfaces:

- same field names,
- same labels,
- same sections,
- same clinical meaning,
- same finalized output expectations.

This creates visual parity for staff and stakeholders while preserving a single clinical truth path.

## What "Same Forms" Means In Practice

For this project, "the same forms in Odoo and in the app" should mean:

- clinicians can recognize the same sections and fields in both places,
- Odoo users can review the full case structure without leaving back-office workflows,
- authorized operational users can perform selected administrative updates,
- final clinical correctness still depends on the clinical API.

It should not mean:

- two different systems validating the same clinical rules,
- two different databases independently editing lesions, specimens, or final reports,
- two different sign-off paths,
- manual reconciliation between Odoo records and app records.

## Surface Roles

### Clinician PWA

Primary role:

- primary clinical authoring surface
- optimized workflow for web, tablet, and mobile
- sign-off and report preview surface

### Clinical API And PostgreSQL

Primary role:

- canonical case record
- workflow and validation engine
- final PDF and narrative snapshot generator
- audit and reopen control

### Odoo

Primary role:

- back-office review surface
- operational administration
- user, role, facility, and lookup management where selected
- controlled task coordination
- bridge and integration utilities

## V1 Ownership Matrix

| Field Area | Clinician PWA | Odoo | Canonical Owner | V1 Edit Rule |
| --- | --- | --- | --- | --- |
| Case header | Full draft create and edit | Visible with limited draft support | Clinical API for cases | Odoo may submit controlled draft updates such as assignment or scheduling metadata through the bridge |
| Safety and indication | Full draft authoring | Visible for review | Clinical API | Odoo is read-only in V1 |
| Prep and completeness | Full draft authoring | Visible for review | Clinical API | Odoo is read-only in V1 |
| Segment exam and IBD | Full draft authoring | Visible for review | Clinical API | Odoo is read-only in V1 |
| Lesion log | Full draft authoring | Visible for review | Clinical API | Odoo is read-only in V1 |
| Specimens and plan | Full draft authoring | Visible for review | Clinical API | Odoo is read-only in V1 |
| Follow-up tasks | Create and manage in case context | Visible in operations lists | Clinical API for clinical tasks | Odoo may support assignment and status actions only through bridge calls |
| Final report snapshot and PDF | Preview and export | Archive and open attached PDF | Clinical API | Read-only after finalization everywhere |
| Users, facilities, and lookup dictionaries | Consume synchronized values | Primary admin surface if chosen | Odoo when explicitly designated | Odoo can own these reference datasets and sync them to the API |
| Reopen controls and admin overrides | Controlled action surface | Operational request surface | Clinical API | Odoo may initiate a reopen request, but the clinical API decides and records it |

## Recommended V1 Rule By Data Category

### Clinical-Owned Data

These fields should be stored, validated, and versioned only in the clinical service:

- case header values once a case exists
- safety and indication
- colonoscopy preparation and completeness
- segment exam and IBD activity
- lesion rows
- specimen rows
- impression and follow-up plan
- final narrative snapshot
- final PDF reference
- clinical follow-up tasks

### Odoo-Owned Reference Data

These records may originate in Odoo and sync into the clinical stack:

- users
- groups and role mappings
- facilities and units
- selected lookup dictionaries approved for centralized administration

### Derived Or Mirrored Data

These should be displayed in Odoo but not treated as independently editable:

- case status
- validation readiness summary
- finalized timestamp
- finalized by
- generated report preview metadata
- audit summary counters

## Sync Direction Rules

### PWA To API

- All clinical editing from the app writes directly to the clinical API.
- The API validates, persists, versions, and audits the change.

### API To Odoo

- Odoo receives case mirrors, summary fields, task summaries, and finalized report metadata.
- Sync must be idempotent using the clinical case UUID as the external key.
- Finalized cases should continue syncing into Odoo as locked records for archive and operations visibility.

### Odoo To API

- Odoo may write only through approved bridge endpoints.
- Odoo-originating writes should be limited to reference data, selected operational updates, and controlled admin actions in V1.
- Odoo must not directly overwrite clinical draft or finalized data in its own database and later "push" it as if it were canonical.

## Conflict Rules

- Clinical API wins for every clinical field.
- Odoo wins only for datasets explicitly designated as Odoo-owned reference data.
- If a case is finalized, both surfaces must treat clinical fields as locked unless the clinical API reopens the case.
- Any stale update must be rejected using version or updated-at checks.

## Odoo Module Design Guidance

### Mirror Model Pattern

Build the Odoo module around a mirror-first structure:

- `phd.ass.case`
- `phd.ass.case.segment`
- `phd.ass.case.lesion`
- `phd.ass.case.specimen`
- `phd.ass.followup.task`
- `phd.ass.sync.event`

Recommended root fields on `phd.ass.case`:

- `external_case_id`
- `case_status`
- `procedure_type`
- `patient_identifier`
- `procedure_datetime`
- `facility_unit`
- `endoscopist_user_id`
- `finalized_at`
- `finalized_by_user_id`
- `pdf_attachment_id` or external PDF reference
- `last_synced_at`
- `payload_version`
- `clinical_payload_json` for raw traceability if useful

Use Odoo child models for repeatable structures so the Odoo interface can show the full clinical layout without inventing new field meanings.

### Form Layout Guidance In Odoo

Mirror the app structure with tabs or notebook pages:

- Case Header
- Safety
- Prep And Completeness
- Segment Exam
- Lesion Log
- Specimens And Plan
- Tasks
- Report And Audit

This gives stakeholders the visual parity they want while keeping the workflow understandable for staff.

### Editing Strategy In Odoo

Recommended V1:

- editable in Odoo: user administration, facilities, lookup sets, task assignment metadata, selected case header admin updates
- read-only in Odoo: safety, colonoscopy details, lesions, specimens, impression, report snapshot, finalization data

If later phases require real clinical data entry in Odoo, do not switch to local Odoo-only persistence. Instead:

- render the fields in Odoo,
- submit them to bridge endpoints,
- let the clinical API validate and save them,
- refresh the mirrored Odoo record from the API response.

## UX Implications

- The clinician PWA remains the fastest authoring experience for procedure-time use.
- Odoo becomes a familiar review and operational workspace for admin staff.
- Labels, section names, and ordering should stay aligned across both surfaces.
- Finalized records should show a clear locked state in both surfaces.
- Validation errors should come from the clinical API so users are not trained on conflicting rules.

## Anti-Patterns To Avoid

- storing a second independent lesion table in Odoo and reconciling later
- generating the final clinical PDF in Odoo instead of the clinical service
- allowing Odoo users to edit finalized clinical fields directly
- re-implementing clinical validation logic separately in Python and JavaScript
- letting field labels drift between the app and Odoo

## Build Sequence

1. Keep the clinician PWA and clinical API as the primary clinical workflow path.
2. Build Odoo mirror models and read-only review layouts for all V1 field groups.
3. Add bridge sync for case summaries, child rows, tasks, and finalized report metadata.
4. Add only the narrow Odoo edit actions that belong to operations and reference management.
5. Introduce API-backed Odoo clinical editing only if the business still needs it after the mirror-first workflow is proven.

## Related Documents

- [ADR-002 Self-Hosted Hybrid Odoo Architecture](./ADR-002-self-hosted-hybrid-odoo.md)
- [Integration Boundaries](./INTEGRATION_BOUNDARIES.md)
- [Schema V1](./SCHEMA_V1.md)
- [Data Dictionary V1](../product/DATA_DICTIONARY_V1.md)
- [Screen Field Map V1](../product/SCREEN_FIELD_MAP_V1.md)
