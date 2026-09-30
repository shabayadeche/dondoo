# Clinical workflow contract

The clinical API is the authority for permissions and case status changes. The PWA may guide a user, but it must not be relied upon to enforce a clinical rule.

## Case states

| State | Meaning | Next controlled actions |
| --- | --- | --- |
| `draft` | Active documentation | Preview, mark ready for sign-off |
| `draft_reopened` | Finalized record reopened for amendment | Preview, mark ready for sign-off, return to draft |
| `ready_for_signoff` | Validation complete and awaiting clinician sign-off | Finalize, return to draft |
| `finalized` | Immutable clinical record with revision history | Reopen with a reason |

## Permissions

| Action | Permitted role | Required source state |
| --- | --- | --- |
| Preview | Authenticated clinical user | Draft, reopened draft, or ready for sign-off |
| Mark ready for sign-off | Authenticated clinical user | Draft or reopened draft |
| Finalize | Endoscopist | Ready for sign-off |
| Return to draft | Operations or workspace administrator | Ready for sign-off or reopened draft |
| Reopen | Operations or workspace administrator | Finalized, with a reason |

## Required data by stage

- **Create a draft:** patient identifier, case type, procedure date/time, endoscopist, and a resolvable facility.
- **Document the procedure:** clinical fields are saved as a draft and may remain incomplete.
- **Mark ready / finalize:** server validation requires all report-critical clinical fields for the selected procedure.

This contract is implemented in `services/clinical_api/app/workflow.py` and covered by `tests/test_workflow_contract.py`.
