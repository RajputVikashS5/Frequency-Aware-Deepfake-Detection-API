# Frontend Documentation

## Overview

This frontend is a Vite + React browser prototype for a frequency-aware deepfake detection and image forensics workflow. It is designed as a demo-first research interface that demonstrates how spatial RGB cues, 2D FFT spectrum analysis, and Haar DWT wavelet patterns can be visualized in a user-facing analysis flow.

The current implementation remains intentionally frontend-only and local-first. It stores analysis history in browser localStorage and simulates authentication in sessionStorage for prototype evaluation.

## Core Design Goals

- Keep the application demo-mode enabled by default unless a backend is explicitly wired in.
- Present outputs as prototype evidence, not as legal or definitive forensic proof.
- Preserve a backend-ready architecture so future integration can replace the demo service without changing the UI shell.
- Keep all app state in the browser during the current phase, with clear disclosure notices in both the workflow and results views.

## Project Structure

- `src/App.jsx` — route entry point and overall app navigation shell.
- `src/pages/` — route-level pages: Home, Analyze, Results, History, Methodology, Login, Register.
- `src/components/` — reusable UI pieces for layout, upload, results, and history.
- `src/services/` — analysis orchestration and local prototype logic.
- `src/config/appConfig.js` — single source of truth for demo mode, app metadata, and disclaimers.
- `src/utils/` — formatting and validation helpers.

## Runtime Behavior

### Demo mode

The app enables demo mode by default unless `VITE_DEMO_MODE=false` is set in the frontend environment. This is configured centrally in `src/config/appConfig.js`.

When demo mode is active:

- the analysis service routes into the browser-only mock analysis pipeline,
- results are clearly labeled as demo outputs,
- the UI displays a prominent notice that the result is not an actual model prediction,
- the report and summary text remain instructive and prototype-focused.

### Authentication

Authentication is intentionally a UI mock. `src/services/authService.js` stores a current user in `sessionStorage` and simulates login and registration only. It is not a secure backend implementation.

### Analysis history

Historical analyses are stored in browser localStorage via the history service. This is intentionally local to the current browser and not synchronized with a backend or database.

## Route Map

- `/` — Home page
- `/analyze` — image upload and validation flow
- `/results/:analysisId` — forensic result details and supporting visualizations
- `/history` — prior local analyses
- `/about` and `/methodology` — project framing and technical explanation
- `/login` and `/register` — demo auth pages

## Validation and Build

The frontend uses Vite with a build script and an oxlint configuration:

- `npm run build` — production build validation
- `npm run lint` — lint pass for the current frontend codebase

## Important Constraints

- Do not present demo outputs as actual model predictions.
- Keep disclaimers and labels visible in the results workflow.
- Maintain clear separation between prototype UI logic and future real inference integration.
- Prefer local browser storage and UI-side state while the product remains in prototype mode.

## Future Extension Path

The app is structured for a future backend integration without rewriting the presentation layer. When real inference is added, `analysisService.js` will be the natural switch point for replacing the demo pipeline with API-backed execution while preserving the same visual workflow and result pages.
