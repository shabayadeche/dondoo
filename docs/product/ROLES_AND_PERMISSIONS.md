# Roles And Permissions

## Roles

- `endoscopist`
- `nurse`
- `operations_admin`
- `workspace_admin`

## Permission Matrix

| Capability | Endoscopist | Nurse | Operations Admin | Workspace Admin |
| --- | --- | --- | --- | --- |
| Sign in | Yes | Yes | Yes | Yes |
| Create case | Yes | Yes | Yes | Yes |
| Edit draft case | Yes | Yes | Yes | Yes |
| Complete shared safety fields | Yes | Yes | Yes | Yes |
| Complete colonoscopy fields | Yes | Limited | Yes | Yes |
| Edit lesion log | Yes | Limited | Yes | Yes |
| Edit specimen log | Yes | Yes | Yes | Yes |
| Generate preview | Yes | Yes | Yes | Yes |
| Final sign-off | Yes | No | No | No |
| View finalized report | Yes | Yes | Yes | Yes |
| Return ready case to draft | No | No | Yes, with reason | Yes, with reason |
| Reopen finalized report | No | No | Yes, with reason | Yes, with reason |
| Close follow-up tasks | Yes | Yes | Yes | Yes |
| Create or reassign follow-up tasks | Yes | Yes | Yes | Yes |
| Manage users | No | No | Yes | Yes |
| Manage template versions | No | No | Yes | Yes |
| View audit log | Yes | Yes | Yes | Yes |

## Notes

### Limited For Nurse

`Limited` means:

- nurse may update only fields explicitly delegated in workflow,
- nurse may not complete physician-only interpretation fields,
- nurse may not finalize a report.

### Reopen Rule

- only `operations_admin` and `workspace_admin` can return a ready case to draft or reopen a finalized report in V1,
- reopen requires a mandatory reason,
- reopen creates a new audit event,
- reopened case returns to `draft_reopened` status until re-finalized.

## Recommended Ownership

- Endoscopist owns final clinical content and sign-off.
- Nurse owns delegated intake and specimen support fields.
- Operations admin owns operational oversight, templates, users, and controlled reopen actions.
- Workspace admin owns workspace governance and the same controlled admin overrides in V1.
