# Audit And Sign-Off Rules

## 1. Case States

The case lifecycle for V1 is:

- `draft`
- `ready_for_signoff`
- `finalized`
- `draft_reopened`
- `followup_open`
- `followup_closed`

`followup_open` and `followup_closed` are follow-up states layered on top of finalized reporting state.

## 2. Sign-Off Rules

- Only an `endoscopist` may finalize a report.
- Finalization requires all blocking fields to pass validation.
- Finalization stores:
  - signer identity,
  - finalized timestamp,
  - template version,
  - generated narrative snapshot,
  - PDF snapshot reference.

## 3. Blocking Fields

Final sign-off must be blocked when any of these are missing:

- patient identifier
- procedure date and time
- endoscopist
- indication
- consent documented
- team pause completed if required locally
- sedation or anesthesia status
- bowel prep quality
- cecum reached or reason not reached
- segmental examination content
- impression
- communication or follow-up plan

## 4. Reopen Rules

- Reopen is exceptional, not routine.
- Only `operations_admin` and `workspace_admin` may return a ready case to draft or reopen a finalized report in V1.
- Reopen requires:
  - reason,
  - actor identity,
  - timestamp,
  - prior finalized version preserved.
- Reopened reports must be re-finalized by an `endoscopist`.

## 5. Audit Events

The audit log must capture at minimum:

- case created
- draft updated
- field deleted where applicable
- report preview generated
- report finalized
- report reopened
- follow-up task created
- follow-up task reassigned
- follow-up task closed
- template version changed

## 6. Audit Event Shape

Each audit event should capture:

- event ID
- case ID
- actor ID
- actor role
- event type
- event timestamp
- changed entity
- changed field summary
- prior value summary where feasible
- new value summary where feasible
- reason, if required

## 7. Final Report Immutability

- A finalized report is immutable for ordinary users.
- Generated report text used at sign-off must be stored as a snapshot.
- PDF must match the finalized snapshot.
- Template changes must not alter prior finalized reports.

## 8. Follow-Up Rules

- Specimen-bearing cases must create at least one follow-up task.
- Task closure must capture actor and resolution note.
- A case cannot enter `followup_closed` unless all open follow-up tasks are resolved or explicitly cancelled with reason.
