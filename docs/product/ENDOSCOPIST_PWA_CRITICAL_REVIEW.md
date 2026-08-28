# Critical PWA review from an endoscopist perspective

Review date: 28 August 2026

## Overall judgement

The PWA is a credible structured-reporting prototype, not yet a fast procedure-
room documentation tool. It has the right bones—procedure-specific templates,
role-aware queues, audit history, images, specimens, tasks, preview, PDF, and
final sign-off—but a working endoscopist would still need too many taps, too much
scrolling, and too much free text. The current experience is closer to a clean
post-procedure form than a real-time endoscopy companion.

## What is working

- Patient, facility, unit, endoscopist, nurse, status, and audit ownership are
  visible and connected.
- Colonoscopy, EGD, ERCP, and EUS have distinct workflows rather than one generic
  note.
- Finalization is permission-gated and produces a narrative snapshot and PDF.
- Segments, lesions, specimens, images, and follow-up tasks are first-class data.
- The help dock and compact visual system are appropriate for a clinical product.

## P0 — safety and report-integrity gaps

### 1. The PWA does not expose all fields the backend already supports

The API/Odoo model includes insertion time, pathology photodocumentation,
adverse-event occurrence and note, surveillance-interval rationale, resection
technique, tattoo details, hemostasis/closure, IBD fields, and other structured
data. The PWA does not render several of these. This creates a dangerous false
appearance of completeness: a report can pass through the interface without the
endoscopist seeing fields that matter for quality, complications, or follow-up.

### 2. Colonoscopy quality controls are incomplete

BBPS segment fields exist, but there is no clear automatic total/calculation or
interpretation. Cecal landmarks and cecal photography are optional toggles, and
withdrawal time is merely an input. The product does not make the evidence easy
to capture at the moment it occurs.

ASGE/ACG quality guidance identifies bowel-prep adequacy, cecal intubation and
photodocumentation, withdrawal time, lesion details/resection method, and
surveillance adherence as key measures. The current PWA should make these
structured, visible, and auditable rather than optional afterthoughts.

### 3. Patient identity verification is too weak

The start form has one patient identifier plus DOB/age and sex, but no explicit
“two identifiers verified” action, wristband/registration confirmation, or
high-risk mismatch warning. A typo in an identifier should be harder to submit
than it is today.

### 4. The final report review is not a true sign-off workspace

The endoscopist sees the form and a narrative preview, but not a compact
“what changed / what is missing / what will be communicated” review. Sign-off
should be a deliberate final checklist, not the last button at the bottom of a
long page.

## P1 — procedure-room efficiency gaps

### 5. The form is still too long for real-time use

Patient context, safety checks, procedure fields, findings, lesions, specimens,
images, tasks, and controls are stacked vertically. A clinician working from a
tablet must scroll through unrelated sections. Add phase-based navigation:
**Pre-check**, **Procedure**, **Findings**, **Specimens/images**, **Plan/sign-off**.
Keep a sticky patient/status bar and show completion per phase.

### 6. No autosave or interruption recovery signal

The user can save a draft, but there is no prominent “Saved 12:42” state,
background save, offline queue, or conflict message. Endoscopy rooms have
interruptions and unreliable connectivity. Losing a finding is unacceptable.

### 7. No fast-entry methods

There is no voice dictation, keyboard shortcut layer, barcode/wristband scan,
procedure timer, quick-pick phrase, or reusable personal template. Dragon Medical
One explicitly supports dictation, saved text blocks, templates, and custom voice
commands; those are the baseline patterns clinicians now expect from a serious
documentation tool.

### 8. Lesions, images, and specimens are not tightly linked

The PWA stores each collection, but the capture flow does not force or simplify
the relationship between “lesion 1”, its photo(s), resection method, specimen
container, and pathology task. Add a single lesion workflow that creates these
links and labels them consistently.

### 9. No copy-forward or comparison with prior examinations

Past cases can be found, but the active report does not show prior findings,
prior pathology, prior surveillance interval, or “changed since last exam”.
Endoscopists need history as context, with explicit safeguards against copying
stale text into a new report.

## P1 — clinical completeness gaps by procedure

- **Colonoscopy:** add insertion time, automatic BBPS total, bowel-prep scale
  explanation, withdrawal timer, cecal landmark/photo capture, lesion size/shape/
  location/resection method, tattoo and hemostasis fields, and interval rationale.
- **EGD:** add explicit photo documentation of standard landmarks, retroflexion,
  second-duodenum extent, biopsy site/container links, and complication capture.
- **ERCP:** add cannulation details, contrast/radiation dose where available,
  device/stent identifiers and planned removal date, adverse events, and a clear
  post-ERCP monitoring plan.
- **EUS:** add lesion measurements, station/anatomy mapping, needle/device,
  specimen/container linkage, preliminary result, and complication plan.

## P2 — workflow and usability gaps

- Cases search is mostly free-text; add filters for date range, facility, status,
  procedure, pathology pending, and tasks due today.
- “My patients” is derived from accessible cases, not a complete longitudinal
  patient record. Make the patient timeline explicit and include all related
  reports, images, pathology, communications, and tasks.
- Use one consistent term for “ready for sign-off”, “in review”, and “finalized”.
- Show unsaved changes and disable navigation only when a save is genuinely in
  progress; never leave the clinician guessing.
- Add a touch-friendly procedure-room mode with larger controls and reduced
  decorative content.
- Add a visible keyboard/focus order test, 200% zoom test, and screen-reader
  labels for every icon-only action.

## Recommended delivery order

1. Expose every backend clinical field in the PWA and add missing sign-off rules.
2. Build phase navigation, sticky patient context, autosave, and interruption
   recovery.
3. Add the lesion/photo/specimen linked workflow and colonoscopy timers/metrics.
4. Add final sign-off checklist with missing-data and communication review.
5. Add prior-record comparison, filters, personal templates, and voice/shortcut
   support.
6. Pilot with at least three endoscopists during live lists; measure time to open,
   time to complete, missing-field rate, correction rate, and post-procedure
   documentation time.

## External benchmarks used

- [ASGE/ACG colonoscopy quality indicators](https://www.asge.org/home/resources/publications/journal-scan/issue/asge-acg-quality-task-force-updates-quality-indicators-for-colonoscopy)
- [AGA strategies for screening and surveillance colonoscopy](https://gastro.org/clinical-guidance/strategies-to-improve-quality-of-screening-and-surveillance-colonscopy/)
- [Microsoft Dragon Medical One: dictation, templates, and commands](https://support.microsoft.com/en-us/dragon-medical-one/introduction-to-dragon-medical-one)
- [NHS digital typography guidance](https://service-manual.nhs.uk/design-system/styles/typography)
