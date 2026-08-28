# Dondoo branding guide

Version 1.0 · 28 August 2026

This is the shared visual and verbal reference for the Dondoo PWA, Odoo workspace,
reports, exported PDFs, and future patient-facing surfaces. It is designed for
endoscopy teams who scan information quickly, work under interruption, and need
the interface to feel trustworthy without becoming institutional or intimidating.

## 1. Brand position

**Promise:** make every endoscopy record clear, connected, and ready for the next
safe action.

**Personality:** calm, exact, human, dependable.

**Experience goals**

- A clinician should understand patient, procedure, owner, and status at a glance.
- A nurse or coordinator should always know the next task and who owns it.
- A patient should encounter plain, respectful language and no unnecessary alarm.
- A reviewer should be able to distinguish draft, verified, and finalized information.

Avoid visual language that feels playful, luxury, emergency-room red, or like a
generic finance dashboard.

## 2. Logo and naming

Use **Dondoo** as the product name, with a capital D in prose and the lowercase
wordmark only where the supplied asset requires it. The mark represents a record
moving through a continuous care pathway.

Assets:

- [Dondoo mark](../../apps/pwa/public/brand/dondoo-mark.svg)
- [Dondoo logo lockup](../../apps/pwa/public/brand/dondoo-logo.svg)
- [Dondoo app icon](../../apps/pwa/public/brand/dondoo-app-icon.svg)

Rules:

- Keep clear space equal to the width of the mark's stem.
- Use the teal mark on light surfaces or the reversed mark on deep teal.
- Never stretch, rotate, add a shadow, or place it over clinical imagery.
- Do not use the logo to imply a clinical result or endorsement.

## 3. Color tokens

Use semantic tokens in code; do not introduce one-off hex values in screens.

| Token | Hex | Role |
| --- | --- | --- |
| Canvas | `#F4EFE8` | Main app background |
| Canvas alt | `#FAF6EF` | Secondary background and page bands |
| Paper | `#FFFDF8` | Cards, forms, tables, reports |
| Paper soft | `#F3EDE3` | Quiet grouping surfaces |
| Ink | `#213043` | Headings and primary text |
| Slate | `#667384` | Supporting text and metadata |
| Teal | `#2F7B74` | Primary action, links, focus, brand |
| Teal deep | `#214F58` | Hover/pressed state and reversed surfaces |
| Teal soft | `#DEEDE8` | Selected or informational background |
| Success | `#2F6D44` | Confirmed, finalized, complete |
| Warning | `#8A6208` | Attention, due soon, incomplete |
| Critical | `#9E4C43` | Error, destructive, blocked |

Accessibility rules:

- Normal text must meet WCAG 2.2 AA contrast (4.5:1); large text must meet
  3:1. Aim higher for clinical data and outdoor/tablet use.
- Teal, success, warning, and critical are never the only indicator. Pair color
  with a label, icon, or state text.
- Use dark text on soft status backgrounds. Do not put small white text on
  warning yellow.
- Test the actual component state, including hover, focus, disabled, and errors.

The NHS service manual similarly requires consistent typography and at least
4.5:1 contrast for normal text; use its colour and typography guidance as a
quality benchmark, not as a reason to copy NHS identity.

## 4. Typography

Primary typeface: **Atkinson Hyperlegible Next**, with `Segoe UI` as the local
fallback. It is friendly at small sizes and remains legible in dense clinical
lists.

| Style | Size | Weight | Use |
| --- | --- | --- | --- |
| Display | 32–40px | 700 | Login or workspace hero only |
| Page heading | 24–30px | 700 | One per screen |
| Section heading | 18–22px | 700 | Panels and clinical sections |
| Body | 16px | 400 | Instructions and narrative |
| Control text | 15–16px | 600 | Buttons, inputs, tabs |
| Metadata | 13–14px | 600 | Dates, identifiers, timestamps |

Use sentence case. Do not use all caps for patient information, warnings, or
workflow actions. Keep line length near 60–75 characters and use short labels.

## 5. Layout and interaction

- Use an 8px spacing rhythm (8, 16, 24, 32px) with 12–16px card radii.
- Keep patient context at the top: name/identifier, procedure, facility,
  endoscopist, and status.
- Give each panel one primary action. Secondary actions are quieter and grouped.
- Use warm background surfaces for navigation and white paper surfaces for data.
- Preserve the same hierarchy on mobile; do not hide patient identity or status
  behind an overflow menu.
- Make touch targets at least 44×44px and keep destructive actions separated.
- Focus rings are visible teal outlines with a 2px offset; never remove them.
- Motion is brief and functional (150–200ms). Never animate clinical results.

## 6. Components

**Buttons:** teal filled for the primary action, outlined/neutral for secondary,
critical red only for irreversible actions. Labels describe the outcome: “Save
draft”, “Submit for review”, “Finalize report”. Avoid “Click here”.

**Status:** show a text label plus an optional icon. Recommended labels are
`Draft`, `In review`, `Changes requested`, `Finalized`, `Overdue`, and `Blocked`.

**Forms:** labels sit above fields; examples are separate helper text; errors are
shown beside the field and summarized at the top. Never clear entered clinical
data after validation fails.

**Tables and queues:** align identifiers and dates consistently, keep the status
column near the patient context, and provide a visible empty state with the next
action.

**Confirmation:** after saving or submitting, show an inline confirmation that
states what happened and what comes next. Toasts may supplement this but must not
be the only confirmation.

## 7. Clinical content and safety

- Prefer “Endoscopist”, “Facility”, “Procedure date”, and “Report status” over
  internal database terms.
- Use plain language and active voice. Explain an acronym the first time.
- Never imply that a draft is a diagnosis or that an assignment is a completed
  review.
- Display timestamps with timezone where actions cross facilities.
- Keep audit history readable: who, what, when, and previous/new value.
- Patient identifiers should be masked in notifications and non-clinical previews.
- Use respectful, person-first language and avoid blame in error copy.

## 8. Imagery and iconography

The product is data-first. Prefer the mark, simple line icons, and restrained
illustrations over stock clinical photography. Icons must have accessible labels
and should reinforce, not replace, text. Do not use imagery that shows invasive
procedures in login or empty states.

## 9. PWA and Odoo implementation

Both clients must consume the same semantic names:

```ts
canvas, canvasAlt, paper, paperSoft, ink, slate,
teal, tealDeep, tealSoft, success, warning, critical
```

The PWA maps these to CSS custom properties in `apps/pwa/src/styles.css`.
The shared package maps them in `packages/ui/src/tokens.ts`.
The Odoo theme maps teal to `$o-brand-primary` and `$o-action`, with ink/slate
for text and the warm canvas/paper values for webclient surfaces. Keep Odoo's
functional semantics (success, warning, danger) but use the Dondoo values above.

Before release, check both clients at 320px, 768px, and desktop widths; keyboard
navigation; 200% zoom; reduced motion; and light/dim display conditions.

## 10. Governance checklist

Before adding a component or campaign asset, confirm:

1. It uses an existing semantic token and type style.
2. Its purpose is understandable without color, icons, or animation.
3. It has a keyboard focus state and a text alternative.
4. It preserves patient context and does not expose more data than the role allows.
5. It has been reviewed at the PWA and Odoo breakpoints.

Reference standards: [NHS colour guidance](https://service-manual.nhs.uk/design-system/styles/colour),
[NHS typography guidance](https://service-manual.nhs.uk/design-system/styles/typography),
and [NHS accessible information requirements](https://www.england.nhs.uk/long-read/accessible-information-standard-requirements-dapb1605/).
