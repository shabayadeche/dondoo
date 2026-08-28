# Dondoo Brand Guidelines

> This earlier quick reference is retained for compatibility. The canonical,
> implementation-ready guide is [DONDOO_BRANDING_GUIDE.md](DONDOO_BRANDING_GUIDE.md).

## Brand Intent

Dondoo should feel calm, exact, and human. The visual system is built for clinical work where users scan quickly, make decisions under time pressure, and need confidence more than decoration.

## Core Traits

- Calm: warm surfaces, restrained contrast blocks, and no overly bright accent colors
- Direct: clear hierarchy, short labels, and one dominant action per panel
- Dependable: rounded geometry, stable spacing, and consistent state colors
- Human: softer neutrals and supportive copy instead of hard-edged enterprise styling

## Logo System

- Primary mark: a rounded lowercase `d` followed by two circular counters, forming a minimal `doo` rhythm
- Meaning: the stem anchors the record, while the three rounded counters suggest continuity, flow, and follow-through
- Default use: place the mark on warm neutral surfaces or on Dondoo Teal for install icons
- Clear space: keep at least the width of the logo stem around the mark
- Do not stretch, rotate, recolor with unrelated hues, or place it over noisy imagery

Primary assets:

- UI mark: [apps/pwa/public/brand/dondoo-mark.svg](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/apps/pwa/public/brand/dondoo-mark.svg)
- App icon source: [apps/pwa/public/brand/dondoo-app-icon.svg](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/apps/pwa/public/brand/dondoo-app-icon.svg)

## Color System

| Token | Hex | Use |
| --- | --- | --- |
| Dondoo Canvas | `#F4EFE8` | app background, large surfaces |
| Dondoo Canvas Alt | `#FAF6EF` | secondary page backgrounds |
| Dondoo Paper | `#FFFDF8` | cards, forms, elevated surfaces |
| Dondoo Ink | `#213043` | primary text, headers |
| Dondoo Slate | `#667384` | secondary text, labels, helper copy |
| Dondoo Teal | `#2F7B74` | brand mark, primary actions, active states |
| Dondoo Teal Deep | `#214F58` | pressed states, strong emphasis |
| Dondoo Teal Soft | `#DEEDE8` | selected backgrounds, low-emphasis highlights |
| Success | `#2F6D44` | confirmed actions, completed states |
| Warning | `#8A6208` | attention states, incomplete work |
| Critical | `#9E4C43` | errors, destructive actions |

## Typography

- Primary UI typeface: Atkinson Hyperlegible Next
- Headings: medium to bold weights, compact line-height, no decorative styling
- Body copy: short paragraphs, support scanning, avoid long explanatory blocks inside dense clinical screens
- Labels: sentence case where possible; all-caps is reserved for very small supporting metadata only

## Product UI Rules

- Keep one primary action visible per panel
- Prefer grouped cards over long uninterrupted forms
- Use warm neutrals for most surfaces and reserve teal for action and focus
- Keep status colors semantic; never reuse warning or critical colors as decoration
- Prioritize scan order: patient and procedure context first, then workflow state, then secondary details
- Avoid ornamental gradients inside data-heavy panels; atmosphere belongs in the page background, not the charting surface

## Interaction Notes

- Focus rings should use a soft teal outline with clear offset
- Motion should be brief and functional, not celebratory
- Empty states should guide the next task in plain language
- Mobile layouts should preserve the same hierarchy rather than hiding critical context behind extra taps
