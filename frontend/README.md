# ImageForensics AI — Frontend Application

Academic research frontend for **Frequency-Aware Deepfake Detection and Image Forensics Using Spatial-Frequency Fusion**.

This client application provides a dark-navy forensic dashboard that visualizes spatial RGB features alongside 2D Fourier (FFT) log-magnitude spectra, Haar discrete wavelet (DWT) subband energy, and radial power-law falloff profiles.

---

## Key Features

- **Multi-Branch Forensic Visualizations**: Centered 2D Fast Fourier Transform (FFT) magnitude spectrum, Haar discrete wavelet (DWT) decomposition (LL, HL, LH, HH), and Error Level Analysis (ELA) heatmaps.
- **Client-Side File Validation Pipeline**: Enforces 10 MB maximum upload size, strict MIME-type & extension validation (`.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`), and image decode validation with safe Object URL revocation.
- **Dual Operating Modes**:
  - **Demo Mode (`VITE_DEMO_MODE=true`)**: Generates client-side forensic decompositions and illustrative prototype metrics, clearly labeled with disclaimers.
  - **Diagnostic API Mode (`VITE_DEMO_MODE=false`)**: Consumes the FastAPI backend `/api/v1/analyze` endpoint. Displays diagnostic extractions, forensic findings, and metadata without computing or claiming a deepfake classification verdict.
- **Local History Management**: Preserves inspection history locally within browser `localStorage` and active session cache with verdict filtering and record clearing.
- **Accessible Dark Design System**: Charcoal/slate palette with cyan, blue, and violet forensic accents conforming to WCAG contrast standards, keyboard focus rings, and screen-reader accessibility labels.
- **Simulated Authentication**: Prototype sign-in and registration flows with password visibility toggles, strength indicators, and session storage tokens.

---

## Quickstart

### 1. Prerequisites
- Node.js >= 18
- npm >= 9

### 2. Installation
```bash
cd frontend
npm install
```

### 3. Local Development Server
```bash
npm run dev
```
The application will be available at `http://localhost:5173`.

### 4. Running the Test Suite
Run all unit and component integration tests using Vitest and React Testing Library:
```bash
npm test
```
To run tests in interactive watch mode:
```bash
npm run test:watch
```

### 5. Production Build
```bash
npm run build
npm run preview
```

---

## Backend Integration (FastAPI)

When connecting the frontend to the actual backend diagnostic service:

### 1. Configure Environment Variables
Copy `.env.example` to `.env` in the `frontend` directory:
```env
VITE_DEMO_MODE=false
VITE_API_BASE_URL=http://localhost:8000
VITE_ENABLE_AUTH=true
VITE_APP_NAME="ImageForensics AI"
```

### 2. Start the Backend API Server
From the project root:
```bash
# Activate python virtual environment
.venv\Scripts\activate   # Windows
# or: source .venv/bin/activate # Linux/macOS

# Start FastAPI uvicorn server
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Diagnostic-Only Scope
> **IMPORTANT NOTE**: The current backend endpoint `/api/v1/analyze` operates in **Diagnostic Mode**. It isolates facial regions and produces multi-branch spatial and frequency decompositions. **No deepfake classification verdict or confidence score is produced by the model in this phase.** The frontend displays a **Diagnostic Only** badge and disables classifier verdict cards accordingly.

---

## Directory Structure

```text
frontend/
├── dist/                      # Production build output
├── public/                    # Static assets
├── src/
│   ├── app/
│   │   ├── router.jsx         # Centralized React Router configuration
│   ├── components/
│   │   ├── common/            # ConfidenceBar, ConfirmDialog, EmptyState, ScoreCard, PredictionBadge
│   │   ├── history/           # HistoryTable, HistoryFilters
│   │   ├── layout/            # Navbar, Footer, PageLayout, DemoBanner
│   │   ├── results/           # FrequencySpectrumViewer, WaveletViewer, SpectralChart, AnalysisSummary
│   │   └── upload/            # ImageDropzone, ImagePreview, FileMetadata, ValidationMessage
│   ├── config/
│   │   └── appConfig.js       # Central configuration, feature flags, limits, disclaimers
│   ├── pages/
│   │   ├── HomePage.jsx       # Hero, multi-branch overview, pipeline diagram
│   │   ├── AnalyzePage.jsx    # Image intake, dropzone, validation, in-memory processing
│   │   ├── ResultsPage.jsx    # Forensic canvas, diagnostic banner, spectrum viewer
│   │   ├── HistoryPage.jsx    # Inspection audit log, search, filters
│   │   ├── Methodology.jsx    # Scientific theory, mathematical foundations, pipeline flowchart
│   │   ├── LoginPage.jsx      # Prototype login with validation and password toggle
│   │   └── RegisterPage.jsx   # Prototype registration with password strength hints
│   ├── services/
│   │   ├── analysisService.js # Facade dispatching to demoService or FastAPI apiClient
│   │   ├── api.js             # Axios client instance with base URL and timeout
│   │   ├── authService.js     # Simulated session auth with sessionStorage tokens
│   │   ├── demoService.js     # Client-side 2D canvas FFT & DWT decomposition
│   │   ├── historyService.js  # LocalStorage history management with session caching
│   │   └── reportService.js   # Printable forensic PDF and text summary generator
│   ├── test/
│   │   └── setup.js           # Vitest setup with jest-dom matchers and canvas polyfill
│   ├── utils/
│   │   ├── fileValidation.js  # Size, MIME, extension, and decode validators
│   │   └── formatters.js      # Date and byte formatters
│   ├── App.jsx                # Main application component mounting AppRoutes
│   ├── index.css              # Tailwind utilities, root dark theme, custom scrollbar
│   └── main.jsx               # Application entrypoint
├── FRONTEND_DOCUMENTATION.md  # Comprehensive architecture & design system specification
├── package.json               # Scripts, dependencies, and vitest config
├── tailwind.config.js         # Semantic design tokens (canvas, card, border, accents)
└── vite.config.js             # Vite configuration with jsdom test environment
```
