# Dondoo interface and icon standard

## Purpose

Dondoo is a clinical workspace. Its interface should feel calm, familiar and fast while keeping clinical decisions unambiguous. This standard applies to the PWA and any matching Odoo custom views.

## Action hierarchy

Use the action’s clinical impact to determine its presentation.

| Action type | Presentation | Examples |
| --- | --- | --- |
| Clinical state change or irreversible action | Labelled button with an icon | Save draft, mark ready for sign-off, finalize report, return to draft, reopen finalized case |
| Common, reversible utility | Icon-only control with an accessible name and tooltip | Back, close, search, filter, preview |
| Low-frequency secondary action | Labelled option in an overflow menu | Open finalized PDF, back to list, download, attachment utilities |

Do not make a clinical state change icon-only. A user must be able to understand an action without relying on icon recognition.

## Icon rules

- Use one consistent rounded-outline icon family. New icons should match the existing Dondoo stroke weight, corner treatment and optical size.
- Use icons to reinforce a short label; they must not replace a label for a workflow decision.
- Every icon-only control needs an `aria-label` and a `title` tooltip. The visible hit target is at least 44 by 44 pixels; use a 22–24 pixel icon inside it.
- Use neutral icon colour by default. Accent colour indicates the primary action; status colours must reinforce a readable status label, never be its only meaning.
- Keep destructive and finalizing actions visibly separate from routine utilities. Do not use red simply to make a control more noticeable.

## Case controls

The control panel should follow this order:

1. **Save draft** — primary, always labelled.
2. **Preview** — accessible icon-only utility.
3. **Mark ready for sign-off** — labelled workflow transition.
4. **Finalize report** — labelled primary action, shown only when permitted.
5. **Return to draft** or **Reopen finalized case** — labelled status correction, with a reason where required.
6. **More actions** — overflow for finalized PDF and navigation back to the case list.

The supporting text should be short: “Save, preview, then sign off.” It is guidance, not a second instruction manual.

## Content and layout

- Prefer concise, task-specific language over explanatory paragraphs.
- Put the current task and its primary action first. Move reference material, guidance and low-frequency controls out of the main action path.
- Avoid duplicate status cards and oversized headers. Keep the top bar to brand, useful context and essential global actions.
- On mobile, action groups wrap and remain clear of fixed navigation or floating controls.

## Help

- The dashboard uses a compact **Need help?** control, not a long generic guide. It routes directly to starting a case, finding a case or reviewing tasks.
- Put short guidance next to complex form fields and status transitions, where the decision is made.
- Do not make a chatbot the primary source of workflow guidance. Any future assistant must be optional and must not replace explicit clinical workflow controls.

## Clinical colour system

- **Deep navy** (`#16324F`) is the trusted foundation for primary text and the application header.
- **Clinical teal** (`#167C80`) is the primary interactive colour for actions, focus and active navigation. **Soft aqua** (`#E7F5F3`) supports selected or quiet states.
- **Green** (`#19724A`) communicates completed or finalized status; **amber** (`#8A5A10`) communicates attention or ready-for-sign-off; **red** (`#B42318`) is reserved for errors, urgency and destructive actions.
- **Soft white and slate neutrals** provide calm surfaces and readable secondary content.
- Colour reinforces a readable text label and icon; it is never the sole indicator of case status. Text and controls must meet WCAG contrast requirements on their rendered surface.

## Review checklist

Before merging an interface change, confirm:

- Can a clinician identify every state-changing action from its text alone?
- Does every icon-only control have an accessible name, tooltip and adequate hit target?
- Are secondary actions grouped rather than competing with the primary action?
- Is status communicated by readable text as well as colour or icon?
- Does the view remain usable on a narrow mobile viewport without controls being obscured?
