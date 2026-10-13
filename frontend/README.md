# Frequency-Aware Deepfake Detection Frontend

This project is the React + Vite frontend for a frequency-aware deepfake detection and image forensics prototype. The app demonstrates a browser-first workflow that analyzes uploaded images using spatial, FFT, and DWT-inspired forensic cues while clearly labeling demo-mode outputs as prototype data.

## What this app does

- allows users to upload JPEG, PNG, or WebP images,
- validates local file constraints in-browser,
- runs a browser-side demonstration analysis pipeline by default,
- exposes a forensic-style results page with visual evidence and summary findings,
- stores analysis history in local browser storage for local review,
- presents a research-oriented methodology and responsible-use framing.

## Demo-first architecture

This frontend is intentionally built for demonstration and academic evaluation. It is not yet connected to a secure backend inference service, and the app is designed to clearly indicate when it is operating in demo mode.

## Start locally

```bash
cd frontend
npm install
npm run dev
```

## Build and validation

```bash
npm run build
npm run lint
```

## Key directories

- `src/pages` — route-level application views
- `src/components` — reusable UI and result components
- `src/services` — demo analysis, history, and auth services
- `src/config` — app configuration and disclaimers
- `src/utils` — validation and formatting helpers

## Important note

The app is a research prototype. Demo outputs are not actual model predictions and should not be interpreted as definitive forensic evidence.

