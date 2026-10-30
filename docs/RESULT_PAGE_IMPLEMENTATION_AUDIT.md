# Result Page Implementation Audit

## Scope

This audit records the current implementation before the multi-model forensic
dashboard work described in the supplied implementation prompt. The working
tree already contained uncommitted changes when the audit started; those
changes were preserved.

## Existing functionality

- The FastAPI application exposes `POST /api/v1/analyze`, a deprecated
  `POST /predict` compatibility alias, and `GET /health`.
- Uploaded images are validated for content type, decoded safely, bounded by
  byte/dimension/pixel limits, and analyzed with spatial, FFT, Haar DWT, ELA,
  face-crop, metadata, SHA-256, and spectral-profile diagnostics.
- A single `RGBBaselineInference` loader can load one configured checkpoint and
  returns prediction, score, real/fake probabilities, task metadata, model
  version, and latency.
- The frontend stores completed analyses in local history and renders the
  result through `ResultsPage`.
- Existing reusable visual components include `FrequencySpectrumViewer`,
  `WaveletViewer`, `SpectralChart`, `AnalysisSummary`, and `FileMetadata`.
- Text report download and browser print-to-PDF are already implemented.
- Navigation and history pages are already present and should remain unchanged.

## Current result-page surfaces

- `frontend/src/pages/ResultsPage.jsx` is the actual result page.
- `frontend/src/services/analysisService.js` maps the backend response into the
  frontend history model and preserves the original preview URL.
- `frontend/src/components/results/FrequencySpectrumViewer.jsx` renders the
  FFT spectrum image.
- `frontend/src/components/results/WaveletViewer.jsx` renders the tiled Haar
  subbands.
- `frontend/src/components/results/AnalysisSummary.jsx` renders backend
  findings.
- `frontend/src/components/upload/FileMetadata.jsx` renders file metadata.
- `frontend/src/services/reportService.js` generates a text report and invokes
  native printing.

## Existing API response fields

`AnalysisResponse` currently contains:

- status and message
- inference availability
- prediction, score, real probability, fake probability
- score type, model version, checkpoint task, label semantics
- domain warning and processing latency
- file metadata including dimensions, size, SHA-256, face detection, and one
  bounding box
- four visualization data URIs: face crop, FFT spectrum, DWT subbands, and
  spatial heatmap
- spectral profile and textual findings

The schema is configured with `extra="forbid"`, so any expanded response must
be added explicitly to the Pydantic models and frontend mapping together.

## Model checkpoint and preprocessing status

The following checkpoint files exist in the repository:

| Model | Checkpoint |
|---|---|
| CIFAKE RGB | `experiments/rgb-baseline/cifake-image-v2/cifake-rgb-resnet18-best.pt` |
| CIFAKE FFT | `experiments/fft-baseline/cifake-image-v2/cifake-fft-resnet18-best.pt` |
| CIFAKE RGB+FFT fusion | `experiments/fusion-baseline/cifake-image-v2/cifake-fusion-resnet18-best.pt` |
| FaceForensics++ RGB | `experiments/rgb-baseline/faceforensicspp-c23-r2-v1-limited-clean/faceforensicspp-rgb-resnet18-best.pt` |

Only the configured RGB checkpoint is wired into the live API. FFT and fusion
checkpoints are currently used by training/evaluation code but do not have
runtime inference adapters.

Training contracts are not interchangeable:

- RGB uses RGB input with ImageNet normalization.
- FFT uses grayscale `fft2`/`fftshift`/`log1p` magnitude preprocessing, then
  three-channel ImageNet-normalized input.
- Fusion uses aligned RGB and FFT tensors and a trained two-branch ResNet-18
  classifier. Its output must not be reconstructed by averaging other model
  probabilities.
- The CIFAKE checkpoints are trained for the CIFAKE AI-generated-versus-real
  task and must not be presented as FaceForensics++ manipulation detectors.

## Missing functionality

1. Runtime model registry for independent RGB, FFT, and fusion checkpoints.
2. A response contract for per-model results, availability, task metadata,
   calibration status, and model agreement.
3. Grad-CAM or other valid RGB localization using actual activations/gradients.
4. A technically distinct FFT attribution representation; the spectrum itself
   must not be labeled as a spatial heatmap.
5. Interactive image viewer with zoom, pan, opacity, model selection,
   fullscreen, download, face overlay, and patch-grid controls.
6. Expanded RGB statistics, FFT profiles, noise/compression metrics, and
   patch-level analysis.
7. Explicit verdict states including `DIAGNOSTIC ONLY` and `MODEL UNAVAILABLE`,
   with domain and calibration warnings.
8. Recharts model comparison visualizations and model availability indicators.
9. Expanded evidence summary and technical metadata sections.
10. Report generation that includes all available model outputs and limitations.
11. Backend and frontend tests for multi-model contracts and degraded model
    availability.

## Implemented task separation

The API now returns independent `detections` entries for:

- `ai_generated_vs_real`, backed by CIFAKE-compatible RGB, FFT, and fusion
  checkpoints.
- `deepfake_manipulation_vs_authentic`, backed by the configured
  FaceForensics++/ForgeryNet-compatible checkpoints.

Checkpoint task metadata is validated before inference. A checkpoint from the
wrong task is reported as unavailable instead of being relabeled. Deepfake FFT
and fusion entries remain unavailable until compatible external-task
checkpoints are trained and configured.

## Integration problems and risks

- The current backend defaults to a FaceForensics++ checkpoint path while the
  frontend wording and existing CIFAKE checkpoints represent different tasks.
  Task identifiers must remain visible and predictions must not be conflated.
- `ResultsPage` contains diagnostic and classification paths but does not yet
  represent multi-model agreement or unavailable individual models.
- The frontend production build must be run from `frontend`; the repository
  root has no `package.json`.
- The current Python environment cannot collect the backend suite because
  `torchvision` and `pywt` are unavailable in the active interpreter. This is
  an environment/dependency prerequisite, not a result-page assertion failure.
- Existing model loading deliberately avoids fabricated scores. New adapters
  must preserve that behavior and surface load/inference errors explicitly.
- Visualization data URIs can be large. New response fields should be bounded
  and should avoid duplicating the original upload unnecessarily.

## Reusable implementation plan

1. Add typed configuration for the three runtime checkpoints and a model
   registry that reports availability without inventing results.
2. Add independent FFT and fusion inference adapters using the exact training
   preprocessing and checkpoint architectures.
3. Expand the API schemas and analysis response with per-model results,
   availability, verdict state, calibration/domain metadata, face detections,
   and bounded forensic evidence.
4. Add backend tests for model registry behavior, task separation, unavailable
   models, and response validation.
5. Add `ModelComparison` and `ForensicImageViewer` components, then compose
   the existing diagnostics into expandable result sections.
6. Add model comparison charts, evidence cards, limitations, and explicit
   historical benchmark labels.
7. Upgrade text/print reports and frontend service mapping.
8. Run the backend suite in the project environment and run frontend tests and
   the production build from `frontend`.

## Validation baseline

- `pytest -q` was attempted from the repository root and failed during
  collection because the active Python environment lacks `torchvision` and
  `pywt`.
- `npm run build` was attempted from the repository root and failed because
  `package.json` is located under `frontend`.
- The frontend manifest already contains `build` and `test` scripts.
