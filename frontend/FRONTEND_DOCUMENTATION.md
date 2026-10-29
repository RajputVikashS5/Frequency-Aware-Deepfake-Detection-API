# Frontend Technical Documentation — ImageForensics AI

**Frequency-Aware Deepfake Detection and Image Forensics Using Spatial-Frequency Fusion**  
*Academic Research Prototype — Frontend Architecture & Technical Specification*

---

## 1. Project Purpose & Scope

ImageForensics AI investigates the complementary nature of spatial RGB representations and frequency-domain representations (such as 2D Fast Fourier Transform log-magnitude spectra and Haar discrete wavelet transforms) for detecting generative manipulations in facial photography.

Modern generative models (e.g. StyleGAN, diffusion models, latent face swaps) often produce photorealistic spatial outputs while introducing periodic high-frequency harmonics, radial power falloffs, or wavelet energy discrepancies.

### Scope of Current Phase
This development phase concentrates exclusively on the frontend application:
- A responsive, accessible, dark-themed forensic dashboard.
- Dual-mode architecture supporting client-side demonstration data (`VITE_DEMO_MODE=true`) and live FastAPI diagnostic endpoints (`VITE_DEMO_MODE=false`).
- Comprehensive multi-modal forensic inspection canvas (FFT spectrum, Haar DWT subbands, ELA heatmap, and radial spectral energy curves).
- Clear diagnostic status handling: when communicating with the real backend, the UI presents raw diagnostic extractions with a **Diagnostic Only** badge and suppresses deepfake classification verdicts.

---

## 2. Technology Stack & Justification

| Technology | Version | Purpose & Rationale |
| :--- | :--- | :--- |
| **React** | `19.2.8` | Declarative UI library using functional components, state hooks (`useState`, `useEffect`), and strict concurrent rendering. |
| **Vite** | `8.3.0` | Ultra-fast build tool leveraging native ES modules for instantaneous Hot Module Replacement (HMR) and optimized Rollup bundling. |
| **Tailwind CSS** | `3.4.19` | Utility-first styling framework configured with semantic tokens for dark charcoal/slate themes and forensic cyan/violet accents. |
| **React Router DOM** | `7.18.4` | Declarative client-side routing, route parameter handling (`/results/:analysisId`), and deep linking. |
| **Lucide React** | `1.56.0` | Consistent, accessible SVG icon set for forensic tools, state badges, and system actions. |
| **Axios** | `1.20.0` | Promise-based HTTP client for multipart form data submissions to FastAPI endpoints with timeout and error handling. |
| **Recharts** | `3.10.1` | Declarative SVG charting used specifically for the radial frequency energy falloff curve (DC to Nyquist). |
| **Vitest & RTL** | `5.0.4` | Vite-native unit and component test runner with jsdom environment and React Testing Library for regression validation. |

---

## 3. Directory Structure

```text
frontend/
├── dist/                          # Production distribution bundle
├── node_modules/                  # Package dependencies
├── public/                        # Static public assets
├── src/
│   ├── app/
│   │   └── router.jsx             # Route definitions and AppRoutes wrapper
│   ├── components/
│   │   ├── common/                # Shared foundational UI components
│   │   │   ├── ConfidenceBar.jsx  # Optional model score bar
│   │   │   ├── ConfirmDialog.jsx  # Accessible modal confirmation
│   │   │   ├── EmptyState.jsx     # Fallback when data or history is empty
│   │   │   ├── ErrorState.jsx     # Graceful error banner with retry trigger
│   │   │   ├── LoadingSkeleton.jsx# Skeleton shimmer placeholder
│   │   │   ├── PredictionBadge.jsx# Visual status badge (Likely Real / Manipulated)
│   │   │   └── ScoreCard.jsx      # Metric card for RGB, FFT, and DWT scores
│   │   ├── history/               # Inspection log components
│   │   │   ├── HistoryFilters.jsx # Search input, verdict filter, clear button
│   │   │   └── HistoryTable.jsx   # Tabular display of prior inspections
│   │   ├── layout/                # Global shell and structure
│   │   │   ├── DemoBanner.jsx     # Global prototype/diagnostic notice banner
│   │   │   ├── Footer.jsx         # System metadata, links, scientific disclaimer
│   │   │   ├── Navbar.jsx         # Dark-themed header with navigation and auth
│   │   │   └── PageLayout.jsx     # Page wrapper providing sticky nav, banner, footer
│   │   ├── results/               # Results page forensic displays
│   │   │   ├── AnalysisSummary.jsx# Findings bullet points and model version
│   │   │   ├── FrequencySpectrumViewer.jsx # 2D Fourier log-magnitude viewer
│   │   │   ├── SpectralChart.jsx  # Recharts radial energy decay curve
│   │   │   └── WaveletViewer.jsx  # 4-quadrant Haar DWT decomposition viewer
│   │   └── upload/                # Image intake and preprocessing components
│   │       ├── AnalysisProgress.jsx # Animated pipeline stage spinner
│   │       ├── FileMetadata.jsx   # Technical image properties table
│   │       ├── ImageDropzone.jsx  # Drag-and-drop file upload target
│   │       ├── ImagePreview.jsx   # Image thumbnail with dimension readout
│   │       └── ValidationMessage.jsx # Inline error alert for upload rejections
│   ├── config/
│   │   └── appConfig.js           # Centralized configuration, limits, disclaimers
│   ├── pages/
│   │   ├── HomePage.jsx           # Landing page with hero and methodology summary
│   │   ├── AnalyzePage.jsx        # Image selection, validation, and pipeline intake
│   │   ├── ResultsPage.jsx        # Multi-modal forensic canvas and diagnostic badge
│   │   ├── HistoryPage.jsx        # Local browser session audit history
│   │   ├── Methodology.jsx        # Scientific theory and architecture diagram
│   │   ├── LoginPage.jsx          # Prototype login with client validation
│   │   └── RegisterPage.jsx       # Prototype registration with strength hints
│   ├── services/
│   │   ├── analysisService.js     # Unified analysis facade (demo vs API)
│   │   ├── api.js                 # Axios instance with base URL and timeout
│   │   ├── authService.js         # Simulated session auth with sessionStorage tokens
│   │   ├── demoService.js         # Client-side 2D canvas FFT and Haar DWT generator
│   │   ├── historyService.js      # LocalStorage persistence and active session cache
│   │   └── reportService.js       # Text summary download and print CSS launcher
│   ├── test/
│   │   ├── setup.js               # Vitest environment setup and polyfills
│   │   ├── fileValidation.test.js # File validation unit tests
│   │   ├── analysisService.test.js# API response mapping tests
│   │   ├── LoginPage.test.jsx     # Login form interaction tests
│   │   ├── RegisterPage.test.jsx  # Registration validation tests
│   │   └── ResultsPage.test.jsx   # Results view and diagnostic badge tests
│   ├── utils/
│   │   ├── fileValidation.js      # Size, MIME, extension, and decode logic
│   │   └── formatters.js          # Timestamp and byte size formatters
│   ├── App.jsx                    # Root application component mounting router
│   ├── index.css                  # Tailwind directives and print media queries
│   └── main.jsx                   # React 19 root bootstrap
├── .env.example                   # Environment variable template
├── package.json                   # Project manifest and scripts
├── tailwind.config.js             # Semantic color tokens and typography
└── vite.config.js                 # Vite bundler and test configuration
```

---

## 4. Page Specifications & Routing Table

| Route | Page Component | Description |
| :--- | :--- | :--- |
| `/` | `HomePage` | Introduces the research objective, dual-stream spatial-frequency philosophy, interactive workflow overview, and responsible-use framing. |
| `/analyze` | `AnalyzePage` | File drag-and-drop target with instant validation, image preview, metadata summary, and user-triggered pipeline execution. |
| `/results/:analysisId` | `ResultsPage` | Visualizes the forensic decomposition. Automatically shows the **Diagnostic Only** badge and disables classifier scores when backed by real API responses. |
| `/history` | `HistoryPage` | Local browser audit trail of previously evaluated images with text filtering, verdict categorization, individual deletion, and history clearing. |
| `/about` | `Methodology` | Exhaustive scientific documentation: Fourier analysis principles, wavelet decomposition subbands, mathematical energy curves, and pipeline flowchart. |
| `/methodology` | `Methodology` | Alias route directing to `Methodology`. |
| `/login` | `LoginPage` | Simulated authentication with email format regex, password visibility toggle, loading spinner, and error banner. |
| `/register` | `RegisterPage` | Simulated registration with password strength criteria, password matching validation, and show/hide toggles. |
| `*` | `Navigate to="/"` | Fallback route redirecting all unknown paths to the home view. |

---

## 5. Reusable Components Catalog

### Layout Components
- **`Navbar`**: Responsive sticky header rendered across all pages. Features the brand logo, desktop navigation links, optional login/register buttons (controlled by `appConfig.authEnabled`), active route highlighting, and an API health status indicator (hidden in demo mode).
- **`DemoBanner`**: Rendered immediately below the navbar. Highlights that the system is operating in prototype demo mode or real diagnostic mode without an automated classifier.
- **`Footer`**: System metadata, version indicator, navigation shortcuts, and research limitation notices.
- **`PageLayout`**: Shell wrapper applying the dark canvas background (`bg-canvas`), managing container max-width, and binding `Navbar`, `DemoBanner`, and `Footer`.

### Upload & Validation Components
- **`ImageDropzone`**: Accessible drag-and-drop dropzone supporting click-to-browse, drag-hover visual cues, and format guidance.
- **`ImagePreview`**: Renders the selected image thumbnail with natural pixel dimension readouts and action buttons to replace or remove the file.
- **`FileMetadata`**: Clean two-column table displaying filename, byte size, format, and dimensions.
- **`ValidationMessage`**: Warning alert rendered when a selected file violates size, extension, or MIME constraints.
- **`AnalysisProgress`**: High-contrast spinner with sequential stage indicators (intake, Fourier transform, wavelet decomposition, report generation).

### Forensic Result Components
- **`FrequencySpectrumViewer`**: Renders the centered 2D Fourier (FFT) log-magnitude spectrum with interactive quadrant indicators (-Nyquist, +Nyquist, DC center) and an interpretation drawer.
- **`WaveletViewer`**: Renders the 4-quadrant Haar discrete wavelet decomposition: LL (Approximation), HL (Vertical), LH (Horizontal), and HH (Diagonal noise residue).
- **`SpectralChart`**: Recharts radial frequency curve showing azimuthal energy falloff from 0 Hz (DC) to $\pi$ (Nyquist) against natural optical $1/f$ distributions.
- **`AnalysisSummary`**: Diagnostic bullet points detailing detected spectral artifacts, compression boundaries, and model architecture versions.
- **`PredictionBadge`**: Color-coded pill badge displaying verdict (used exclusively for demo evaluations).
- **`ScoreCard`**: Accent-colored metric card displaying branch-specific contribution probabilities.

---

## 6. Design System & Theming

The user interface follows an **Accessible Dark Navy / Charcoal** aesthetic tailored for scientific imaging:

```text
Canvas (Background)      : #0b0f19
Card Surface             : #111827
Card Subtle Surface      : #162032
Card Hover Surface       : #1a273e
Border Default           : #1f293d
Border Bright            : #2d3e58
Primary Accent (Cyan)    : #06b6d4 / #22d3ee (FFT spectral highlights)
Secondary Accent (Blue)  : #3b82f6 / #60a5fa (Spatial RGB stream)
Tertiary Accent (Violet) : #8b5cf6 / #a78bfa (Wavelet DWT decomposition)
Warning / Diagnostic     : #f59e0b / #fbbf24 (Diagnostic only status)
Error / Manipulated      : #ef4444 / #f87171 (Synthetic anomalies)
Success / Authentic      : #10b981 / #34d399 (Natural optical profile)
```

- **Typography**: Clean system stack (`Inter`, `Segoe UI`, `-apple-system`) with monospace accents (`ui-monospace`, `SFMono-Regular`) for numerical metrics, file hashes, and frequencies.
- **Focus Indicators**: Every interactive control includes high-visibility `focus-visible:ring-2 focus-visible:ring-accent-cyan` outlines for full keyboard accessibility.

---

## 7. State Management & Data Flow

```text
[ User Selects File ] 
         │
         ▼
[ fileValidation.js ] ───(Rejects)───► [ ValidationMessage Alert ]
         │
     (Passes)
         ▼
[ AnalyzePage.jsx ] ───(User Clicks "Analyze")───► [ analysisService.js ]
                                                          │
                    ┌─────────────────────────────────────┴─────────────────────────────────────┐
                    ▼                                                                           ▼
           [ VITE_DEMO_MODE=true ]                                                     [ VITE_DEMO_MODE=false ]
                    │                                                                           │
           [ demoService.js ]                                                          [ apiClient.post('/api/v1/analyze') ]
           • Offscreen HTML5 Canvas                                                    • FastAPI Multi-Branch Diagnostic
           • 2D FFT Log Magnitude                                                      • Face Crop & Wavelet Decomposition
           • 4-Quadrant Haar DWT                                                       • raw.status === 'diagnostic_complete'
                    │                                                                           │
                    └─────────────────────────────────────┬─────────────────────────────────────┘
                                                          ▼
                                            [ historyService.saveAnalysis() ]
                                            • Caches in active session Map
                                            • Persists sanitized record in localStorage
                                                          │
                                                          ▼
                                            [ Navigate: /results/:id ]
                                                          │
                                                          ▼
                                                  [ ResultsPage.jsx ]
                                      • If isDiagnostic: True
                                          - Displays "Diagnostic Only" badge
                                          - Hides classifier verdict cards
                                          - Renders multi-modal canvases
                                      • If isDiagnostic: False (Demo)
                                          - Displays demo classification verdict
```

### Safe Object URL Lifecycle
Temporary browser preview URLs (`blob:http://...`) are created with `URL.createObjectURL(file)`. When a user replaces an image, navigates away, or unmounts the preview, `safeRevokeUrl()` calls `URL.revokeObjectURL()` immediately to eliminate memory leaks.

---

## 8. Demo Mode vs. Real Backend API

### Demo Mode (`VITE_DEMO_MODE=true`)
- Operates entirely offline without needing a Python backend.
- Renders authentic-looking 2D FFT spectra and Haar wavelet subbands via an offscreen HTML5 canvas.
- Synthesizes radial frequency profiles and structured findings.
- Explicitly flags all results with `DEMO DATA — NOT AN ACTUAL MODEL PREDICTION`.

### Real Diagnostic API Mode (`VITE_DEMO_MODE=false`)
- Submits `multipart/form-data` with key `file` to `POST /api/v1/analyze`.
- Expects backend response schema:
  ```json
  {
    "status": "diagnostic_complete",
    "message": "Diagnostic feature extraction completed.",
    "model_version": "ResNet18-FFT-DWT-v1.0-diag",
    "inference_available": false,
    "metadata": {
      "filename": "suspect.jpg",
      "filesize_kb": 312,
      "dimensions": "512x512",
      "face_detected": true,
      "sha256": "abcdef1234567890..."
    },
    "visualizations": {
      "face_crop": "data:image/jpeg;base64,...",
      "fft_spectrum": "data:image/jpeg;base64,...",
      "dwt_subbands": "data:image/jpeg;base64,...",
      "spatial_heatmap": "data:image/jpeg;base64,..."
    },
    "spectral_profile": [
      { "frequency": "0.0π", "energy": 95, "idealReference": 95 },
      { "frequency": "0.5π", "energy": 42, "idealReference": 40 }
    ],
    "findings": [
      "2D Fourier log-magnitude spectrum shows elevated high-frequency cross patterns.",
      "Haar diagonal HH subband exhibits synthetic upsampling discrepancy."
    ]
  }
  ```
- The frontend recognizes `raw.status === 'diagnostic_complete'`, marks `isDiagnostic = true`, and sets `isManipulated = null` and `confidencePct = null`.
- The results view replaces the classification card with a prominent **Diagnostic Only** badge and shows the multi-modal decomposition canvases.

---

## 9. Environment Configuration

All environment variables use the `VITE_` prefix:

```env
# Controls whether the frontend runs offline demo simulation or connects to backend
VITE_DEMO_MODE=true

# Base URL for the FastAPI service
VITE_API_BASE_URL=http://localhost:8000

# Enables or disables prototype authentication links in Navbar and routes
VITE_ENABLE_AUTH=true

# Brand display name
VITE_APP_NAME="ImageForensics AI"
```

---

## 10. Testing Strategy & Execution

The frontend maintains automated unit and integration tests powered by **Vitest** and **React Testing Library** in a simulated `jsdom` environment.

### Test Suites
1. **`src/utils/fileValidation.test.js`**
   - Validates acceptance of valid JPEG, PNG, and WebP files under 10 MB.
   - Asserts rejection of files > 10 MB.
   - Asserts rejection of unsupported MIME types (`image/gif`, `application/pdf`).
   - Asserts rejection of malicious or mismatched extensions (`.exe`, `.svg`).
   - Tests image decoding validator and Object URL cleanup.
2. **`src/services/analysisService.test.js`**
   - Mocks `apiClient.post` and verifies mapping into the UI diagnostic schema.
   - Verifies demo mode fallback execution.
3. **`src/pages/LoginPage.test.jsx`**
   - Renders login form, validates required fields and email regex.
   - Tests password visibility toggle button.
   - Tests loading state and error alert banners.
4. **`src/pages/RegisterPage.test.jsx`**
   - Tests email, password, and confirm password validations.
   - Asserts password mismatch error.
   - Verifies password strength checklist.
5. **`src/pages/ResultsPage.test.jsx`**
   - Renders with a mock diagnostic result: verifies **Diagnostic Only** badge is visible and classification verdict card is omitted.
   - Renders with a demo result: verifies classification badge and score cards appear.
   - Tests missing record empty state.

### Running Tests
```bash
# Run all tests once
npm test

# Run tests in interactive watch mode
npm run test:watch
```

---

## 11. Accessibility Considerations

- **Keyboard Navigation**: All interactive elements (links, buttons, dropzone, password toggles) are reachable via `Tab` and exhibit standard `Enter`/`Space` activation.
- **Focus Rings**: High-contrast, custom `focus-visible:ring-2 focus-visible:ring-accent-cyan` outlines ensure keyboard users always know their active element.
- **ARIA Attributes**:
  - `role="status"` and `aria-live="polite"` on `DemoBanner` and `AnalysisProgress`.
  - `aria-label` attributes on icon-only buttons (password eye toggles, mobile menu, report print).
  - Form controls properly associated with `<label htmlFor="...">`.
- **Color Contrast**: All text elements satisfy WCAG 2.1 AA contrast ratios (>= 4.5:1) against their card and canvas backgrounds.

---

## 12. Known Limitations & Roadmap

1. **Model Inference**: The backend may expose raw probabilities from a verified checkpoint. Diagnostic responses do not include model scores, and checkpoint task metadata is shown when inference is enabled.
2. **Client-Side Canvas Resolution**: In demo mode, canvas generation runs at 256x256 pixels for performance reasons. The backend generates high-resolution 512x512 decompositions.
3. **Local History Scope**: Inspection logs reside in browser `localStorage`. When the user clears site data or switches browsers, past records are reset. A persistent database will be added during multi-user backend deployment.
