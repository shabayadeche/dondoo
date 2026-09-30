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
- Every icon-only control needs an `aria-label` and a `title` tooltip. The visible hit target is at least 42 by 42 pixels.
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

## Review checklist

Before merging an interface change, confirm:

- Can a clinician identify every state-changing action from its text alone?
- Does every icon-only control have an accessible name, tooltip and adequate hit target?
- Are secondary actions grouped rather than competing with the primary action?
- Is status communicated by readable text as well as colour or icon?
- Does the view remain usable on a narrow mobile viewport without controls being obscured?

