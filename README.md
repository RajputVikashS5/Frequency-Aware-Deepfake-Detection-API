# TruthLens AI

**Multimodal Fake News Detection and Evidence-Grounded Explainable AI System**

A production-quality frontend for submitting news headlines, article text, and optional images to detect misinformation, with transparent explanations and retrieved evidence.

## Prerequisites

- Node.js 18 or later
- npm (comes with Node.js)

## Installation

```bash
npm install
```

## Development Server

```bash
npm run dev
```

The app runs on `http://localhost:5173` by default.

## Demo Mode

The app starts in **Demo Mode** by default, using sample data — no backend required. You can:

- Navigate all pages
- Submit the analysis form with validation and image upload
- View sample analysis results
- Browse and filter history
- Test the contact form

A banner at the top clearly indicates when Demo Mode is active. Sample predictions are labelled as sample data and never presented as real AI analysis.

## Connecting the Backend

1. Set `VITE_DEMO_MODE=false` in your `.env` file.
2. Set `VITE_API_BASE_URL` to your backend URL (e.g., `http://localhost:8000`).
3. Restart the dev server.

### Expected API Contract

**POST `/api/analyze`** — multipart form data:

| Field          | Type   | Required | Description                          |
|----------------|--------|----------|--------------------------------------|
| `headline`     | string | Yes      | News headline                        |
| `article_text` | string | Yes      | Full article body                    |
| `mode`         | string | Yes      | `text_image` or `text_only`          |
| `source_url`   | string | No       | Original article URL                 |
| `image`        | file   | No       | Image (JPG, PNG, WEBP; max 10 MB)    |

**Response (JSON):**

```json
{
  "analysis_id": "string",
  "verdict": "REAL | FAKE | MISLEADING | UNVERIFIED",
  "confidence": 0.72,
  "explanation": "string",
  "text_analysis": {
    "model_label": "string",
    "confidence": 0.74,
    "explanation": "string",
    "indicators": ["string"]
  },
  "image_analysis": {
    "model_label": "string",
    "confidence": 0.68,
    "explanation": "string",
    "image_text_consistency": "string",
    "manipulation_signals": ["string"]
  },
  "evidence": [
    {
      "source_title": "string",
      "publisher": "string",
      "excerpt": "string",
      "url": "string",
      "classification": "supports | contradicts | insufficient"
    }
  ],
  "created_at": "ISO-8601",
  "mode": "text_image | text_only",
  "headline": "string",
  "article_text": "string",
  "source_url": "string"
}
```

**GET `/api/health`** — returns 200 OK if the service is running.

All fields except `analysis_id`, `verdict`, and `explanation` are optional. The frontend gracefully handles missing `image_analysis`, `evidence`, `confidence`, and other optional fields.

When backend mode is enabled and the backend is unavailable, the app shows a real error — it does not silently fall back to demo data.

## Production Build

```bash
npm run build
```

Output is in the `dist/` directory.

## Type Checking

```bash
npm run typecheck
```

## Linting

```bash
npm run lint
```

## Configuration

All configuration is in `src/config.ts`:

- `apiBaseUrl` — backend URL (from `VITE_API_BASE_URL`)
- `demoMode` — demo toggle (from `VITE_DEMO_MODE`)
- `maxImageSizeBytes` — max upload size (default 10 MB)
- `acceptedImageTypes` — allowed MIME types
- `requestTimeoutMs` — request timeout (default 60s)
- `paginationPageSize` — items per page in history

## Features

- **Home Dashboard** — hero, feature cards, verification pipeline, recent analyses
- **Analyze News** — text + image or text-only mode with drag-and-drop image upload, validation, character counters
- **Processing Screen** — honest indeterminate loading with stage labels
- **Results Dashboard** — verdict card, confidence indicator, text/image analysis, evidence list, explainable AI panel
- **History** — search, filter by verdict, sort, pagination, delete entries, clear all with confirmation
- **About & Methodology** — architecture, pipeline, evaluation metrics, limitations
- **Contact** — feedback form with validation and demo-mode disclosure
- **Dark/Light themes** — dark by default, saved locally
- **Responsive** — mobile sidebar, stacked layouts, touch-friendly
- **Accessibility** — ARIA labels, keyboard navigation, reduced-motion support, semantic HTML

## Project Structure

```
src/
  app/          App component and router
  components/
    layout/     Sidebar, Topbar, Footer, ThemeToggle, AppLayout
    common/     PageHeader, FeatureCard, StatCard, EmptyState, ErrorState, etc.
    analysis/   NewsInputForm, ImageUploader, VerdictBadge, AnalysisProgress, etc.
    evidence/   EvidenceList, EvidenceItem
    history/    HistoryTable
  pages/        Home, Analyze, Results, History, About, Contact, NotFound
  services/     api.ts, analysisService.ts
  hooks/        useTheme, useToast, useHistory, useReducedMotion
  utils/        history, format, resultsStore
  types/        analysis.ts
  data/         demoData.ts
  config.ts
```

## Privacy

- Analysis history is stored only in the current browser's local storage
- Uploaded images are not persisted — they are sent to the backend (if connected) and held in memory only
- No sensitive article content is stored beyond the current session
- External links open safely with `rel="noopener noreferrer nofollow"`
- User-provided content is rendered as escaped text, never with `dangerouslySetInnerHTML`

## Known Limitations

- Demo Mode uses fixed sample data and does not perform real AI analysis
- History and results are browser-local and not shared across devices
- The frontend does not perform backend validation — it validates input format only
- Confidence scores reflect model certainty, not the probability that a claim is objectively true
