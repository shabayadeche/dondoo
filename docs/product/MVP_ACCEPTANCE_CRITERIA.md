# MVP Acceptance Criteria

## Functional Acceptance

### Case Management

- User can create a colonoscopy case.
- User can save as draft and resume later.
- Case list supports filtering drafts and finalized cases.

### Shared Workflow

- Shared safety fields are visible before colonoscopy-specific fields.
- Blocking fields prevent sign-off when missing.
- Validation is shown inline and at review step.

### Colonoscopy

- User can record prep quality, BBPS, cecal completion, segment exam, lesion log, resection details, impression, and follow-up.
- Repeatable lesion rows support at least six entries in V1.

### Reporting

- System generates a readable narrative report from structured fields.
- User can preview the report before finalization.
- Finalized report exports to PDF.

### Audit And Follow-Up

- Finalized report is locked.
- Reopen path exists for unit admin only.
- Specimen-bearing cases support follow-up task creation and closure.
- Audit log records required events.

## Usability Acceptance

- A trained endoscopist can complete a standard case without using external notes to remember system steps.
- Nurse can complete delegated fields without entering physician-only interpretation fields.
- Mobile app supports task review and targeted case review without breaking workflow.

## Pilot Acceptance

- Pilot users confirm the generated note is clinically usable.
- Pilot workflow does not require duplicate entry into another local tool for the same report in the pilot process.
- Stakeholders accept the locked-finalized and reopen rules.

## Release Blocking Defects

Any of the following blocks pilot release:

- missing audit on finalize or reopen,
- invalid PDF output for finalized reports,
- missing blocking validation on required fields,
- inability to save and resume drafts,
- inability to assign or close follow-up tasks,
- role escalation that allows unauthorized finalization.
