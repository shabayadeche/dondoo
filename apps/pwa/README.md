# Clinical PWA Target

This folder is reserved for the installable clinician-facing progressive web app.

## Target Stack

- React
- TypeScript
- PWA manifest and service worker
- Responsive layouts for desktop, tablet, iPhone, and Android

## Intended Role

- primary clinician authoring surface
- installable home-screen experience for iPhone and Android users
- review, follow-up, and targeted completion workflows on mobile

## Current Scope

- dashboard, case queue, and follow-up queue
- start-case flow using live lookup data from the clinical API and Odoo
- case detail editor for colonoscopy, EGD, ERCP, and EUS
- clinician workflow controls for preview, ready-for-sign-off, finalize, return-to-draft, and reopen
- follow-up task status and ownership updates from the same case workspace

## Environment

- Copy `.env.example` to `.env` only if the PWA should call a non-default API origin.
- Leave `VITE_CLINICAL_API_BASE_URL` empty for local Vite proxy development.
- Use [.env.production.example](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/apps/pwa/.env.production.example) as the starting point for production builds.

## Local Run

```bash
npm run dev --workspace @phd-ass/pwa
```

Production build:

```bash
npm run build --workspace @phd-ass/pwa
```

The current local development profile expects:

- PWA on `http://127.0.0.1:4173`
- FastAPI clinical API on `http://127.0.0.1:8000`
- Odoo available behind the clinical API bridge when hybrid mode is enabled

## Production Notes

- Serve the PWA over HTTPS or the installable experience will be degraded on iPhone and Android.
- Keep the PWA, FastAPI service, and Odoo behind one reverse-proxy boundary where possible.
- Use the same-origin Nginx pattern in [deploy/nginx/phd-ass.conf.example](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/deploy/nginx/phd-ass.conf.example) unless there is a strong reason to split origins.
- Use the dedicated task update and case action endpoints instead of writing task closure state through bulk draft sync paths.
- Validate the mobile install flow, login, draft save, sign-off, finalize, and reopen flow on both iOS Safari and Android Chrome before go-live.

## Migration Note

The existing `apps/app` Expo scaffold remains in the repo only as a legacy reference while cleanup and retirement work is completed.
