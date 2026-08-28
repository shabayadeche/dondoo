# Product Requirements Document

## 1. Product Name

Endoscopy Reporting App

## 2. Objective

Build an internal progressive web app for structured endoscopy reporting that runs on web, iPhone, and Android from a shared codebase.

The first release must let clinical staff:

- create a procedure case,
- capture required safety and procedure data,
- complete a structured procedure report,
- generate a narrative note,
- finalize and lock the report,
- track specimens and follow-up tasks.

## 3. V1 Scope

### In Scope

- Authentication and role-based access
- Patient and case creation
- Shared safety and encounter header workflow
- Colonoscopy workflow
- Odoo draft templates for EGD, ERCP, and EUS
- Draft autosave
- Narrative report generation
- PDF export and print support
- Specimen capture
- Follow-up task queue
- Final sign-off and locked records
- Audit log

### Out Of Scope

- PWA-native EGD, ERCP, and EUS sign-off and narrative workflows
- Full EMR replacement
- Billing and coding
- Scheduling
- Full anesthesia documentation
- LIS or EMR integrations
- Offline sync
- Advanced analytics dashboards

Current build note:

- The Odoo clinical workspace now supports structured draft authoring for colonoscopy, EGD, ERCP, and EUS.
- The clinician PWA screen flow, acceptance criteria, and narrative depth remain colonoscopy-first until the other procedure flows are fully designed and approved.

## 4. Primary Users

- Endoscopist
- Assisting nurse
- Unit administrator

## 5. Secondary Users

- Quality reviewer
- Department lead

Quality reviewer functions are phase two unless required for pilot administration.

## 6. User Problems

- Reports are inconsistent between users
- Mandatory safety or quality elements can be missed
- Narrative reporting is slow when entered from scratch
- Specimen and pathology follow-up is difficult to track reliably
- Mobile continuity is weak when teams depend on disconnected tools

## 7. Product Principles

- Structured data first
- Narrative note generated from structured data
- Shared workflow across procedures
- Desktop and tablet optimized for authoring
- Mobile optimized for review, follow-up, and targeted completion
- Final means locked

## 8. Core User Flows

### Flow A: Create And Finalize Case

1. User starts a new procedure.
2. User selects `Colonoscopy`.
3. User selects or enters patient.
4. User completes shared safety section.
5. User completes colonoscopy sections.
6. User reviews generated report.
7. User signs off.
8. System locks record and creates follow-up tasks if needed.

### Flow B: Resume Draft

1. User opens draft from dashboard or case list.
2. User lands on the first incomplete or invalid step.
3. User completes missing fields.
4. User signs off or leaves as draft.

### Flow C: Specimen And Follow-Up

1. User opens tasks.
2. User filters open specimen or pathology tasks.
3. User records action taken.
4. User closes or advances the task.
5. System records the event in the audit trail.

## 9. Functional Requirements

### Authentication And Access

- Users must sign in with role-based access.
- Users may only see actions permitted for their role.

### Case Creation

- User can create a new procedure case.
- Procedure type must be selected before procedure-specific fields appear.
- Case status must support `draft`, `finalized`, and `closed follow-up`.

### Shared Safety Workflow

- Shared safety fields must be completed before final sign-off.
- Missing blocking fields must be visible to the user.

### Colonoscopy Workflow

- Colonoscopy must support structured bowel preparation, completeness, segment exam, lesion logging, resection detail, impression, and follow-up.

### Report Generation

- The system must generate a readable narrative note from structured inputs.
- User must be able to preview the note before sign-off.

### PDF Output

- Finalized reports must support PDF export.
- PDF must reflect the locked finalized state.

### Audit And Sign-Off

- Finalized reports must be locked from ordinary editing.
- Every create, edit, finalize, reopen, and task closure event must be logged.

### Follow-Up

- Specimen-bearing cases must support follow-up task creation.
- Tasks must support owner, due date, status, and resolution note.

## 10. Non-Functional Requirements

- Responsive performance on standard unit hardware
- Support for modern desktop browsers
- Support for iPhone and Android app builds
- Reliable backup and restore path
- Secure access to PHI
- Defined downtime and recovery procedure before production

## 11. Pilot Success Metrics

- Greater than 95 percent mandatory-field completion on finalized reports
- Greater than 90 percent same-day finalization
- Median completion time under 5 minutes after procedure
- All specimen-bearing cases linked to a follow-up state
- Zero final record edits without audit trace

## 12. Risks

- Scope creep into EMR features
- Late changes to sign-off rules
- Excessive mobile scope
- Overuse of free text
- Weak adoption if the workflow is slower than current paper or dictation methods

## 13. Dependencies

- Stakeholder approval of V1 field list
- Stakeholder approval of sign-off and reopen rules
- Pilot users identified
- Device availability for pilot

## 14. Release Decision

V1 is build-ready once the associated data dictionary, permissions matrix, screen-field map, and sign-off rules are accepted.
