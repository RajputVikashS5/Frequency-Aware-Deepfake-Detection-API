# Frequency-Aware Deepfake Image Detection and Forensics

A research-focused project investigating whether **RGB/spatial
features** and **FFT frequency-domain features** can be combined to
classify an individual image as likely real or likely manipulated.

> **Current scope: image detection only.** The website accepts
> individual images. Video upload, video processing, frame timelines,
> temporal models, and video-level predictions are out of scope.
> Video-origin datasets may be used only to prepare still images
> offline, subject to their access terms; samples from the same source
> video must remain in the same data split.

This is an experimental educational project. A model prediction is not
proof that an image is authentic or manipulated.

## Table of contents

-   [Project overview](#project-overview)
-   [Current status](#current-status)
-   [Features](#features)
-   [Technology stack](#technology-stack)
-   [Image-detection architecture](#image-detection-architecture)
-   [Repository structure](#repository-structure)
-   [Development roadmap](#development-roadmap)
-   [Dataset and data-leakage
    strategy](#dataset-and-data-leakage-strategy)
-   [Evaluation plan](#evaluation-plan)
-   [Frontend and API contract](#frontend-and-api-contract)
-   [Installation and run commands](#installation-and-run-commands)
-   [Testing and reproducibility](#testing-and-reproducibility)
-   [Limitations and responsible use](#limitations-and-responsible-use)

## Project overview

### Problem statement

Manipulated and AI-generated images can look realistic. This project
studies whether frequency-domain information provides useful evidence
alongside conventional RGB image features. The research compares an
RGB-only baseline, an FFT-only baseline, and a combined RGB + FFT model.

This is a hypothesis to test, not an assumption: compression, resizing,
sharpening, and camera processing can also affect frequency patterns.

### Objectives

1.  Accept and validate a single image.
2.  Build an RGB-based classifier.
3.  Compute and inspect FFT magnitude representations.
4.  Build an FFT-based baseline classifier.
5.  Combine RGB and FFT features in a fusion model.
6.  Compare models with consistent data splits and metrics.
7.  Display predictions and available forensic visualizations in a local
    web interface.
8.  Document implemented, mocked, tested, and planned functionality
    honestly.

### Out of scope

-   Video upload and video analysis.
-   Inference-time frame extraction.
-   Suspicious-frame timelines.
-   Temporal GRU/Transformer models.
-   Video-level predictions and video-forensics reports.

## Current status

The statuses below reflect the current repository and the validation
commands recorded for this implementation.

  -----------------------------------------------------------------------------
  Area                          Status from available   Required follow-up
                                project notes           
  ----------------------------- ----------------------- -----------------------
  README and project            Being revised           Keep the project
  specification                                         image-only.

  React + Vite frontend         Present                 Verify frontend build
  scaffold                                              and run a production
                                                        build.

  Home and image upload pages   Reported implemented    Verify upload, preview,
                                                        and validation.

  Results and FFT viewer        Exists / needs          Confirm score handling,
                                verification            FFT display, and error
                                                        states.

  Browser-local analysis        Reported implemented    Verify CRUD behavior
  history                                               and explain local-only
                                                        storage.

  Methodology page              Reported implemented    Keep explanations
                                                        image-specific.

  Login/register UI             Previously reported     Add UI-only forms if
                                missing                 still missing; do not
                                                        claim real
                                                        authentication.

  Demo/API service separation   Reported present        Verify demo labels and
                                                        API error behavior.

  `FRONTEND_DOCUMENTATION.md`   Previously reported     Create/update it with
                                missing                 actual implementation
                                                        details.

  Python environment and        Python 3.11 venv        Keep dependencies
  image dataset pipeline        configured; Phase 3    reproducible and run
                                implemented and tested  focused tests.

  FastAPI image                 Needs audit             Implement and test
  upload/validation API                                 missing endpoints and
                                                        validation.

  Real RGB/FFT/fusion inference Not verified; treat as  Do not fabricate
                                not implemented until   predictions.
                                proven                  

  Training and evaluation       Not reported as         Publish metrics only
  results                       complete                after actual
                                                        experiments.
  -----------------------------------------------------------------------------

**Status rule:** File presence alone does not prove a feature works.
Update statuses only after code inspection and relevant checks.

## Features

### Frontend scope

-   Home/landing page.
-   Single-image upload, preview, and validation.
-   Loading, error, and empty states.
-   Results page with prediction and score fields when provided.
-   FFT magnitude-spectrum viewer.
-   Browser-local analysis history.
-   Downloadable or printable report.
-   About/methodology page.
-   Login and registration UI if enabled.
-   Explicit demo labels whenever mock data is shown.

### Research scope

-   RGB-only baseline.
-   FFT-only baseline.
-   RGB + FFT fusion.
-   Optional DWT wavelet analysis after the core baselines.
-   Evaluation and robustness tests.
-   Integration of actual model inference into the API.

## Technology stack

  -----------------------------------------------------------------------
  Technology                          Purpose
  ----------------------------------- -----------------------------------
  Python 3.11                         Image processing, model
                                      development, evaluation.

  PyTorch                             Model training and inference.

  TorchVision                         Image transforms and CNN backbones
                                      such as ResNet18.

  Pillow                              Backend image decoding and
                                      validation.

  OpenCV                              Optional image-processing
                                      utilities; no video ingestion in
                                      this scope.

  NumPy / SciPy                       Numerical and signal-processing
                                      operations.

  PyWavelets                          Optional future DWT features.

  scikit-learn                        Classification metrics and
                                      evaluation.

  Pandas                              Dataset metadata and experiment
                                      summaries.

  Matplotlib                          FFT and experiment visualizations.

  pytest                              Backend and ML utility tests.

  FastAPI / Uvicorn                   Image API and local ASGI server.

  React / Vite                        Frontend and development/build
                                      tooling.

  Tailwind CSS                        Responsive UI styling.

  React Router                        Multipage navigation.

  Axios                               API requests when API mode is
                                      enabled.

  Lucide React                        UI icons.

  Vitest / React Testing Library      Frontend tests if configured.

  Git / GitHub / VS Code              Version control and development.
  -----------------------------------------------------------------------

Install only dependencies needed by the current implementation. Install
PyTorch using the official selector:
https://pytorch.org/get-started/locally/

## Image-detection architecture

``` mermaid
flowchart TD
    A[User selects one image] --> B[Frontend validation and preview]
    B --> C[FastAPI upload endpoint]
    C --> D[Server-side image validation]
    D --> E[Validated image]
    E --> F[RGB branch: spatial features]
    E --> G[FFT branch: frequency features]
    F --> H[Feature fusion]
    G --> H
    H --> I[Classification head]
    I --> J[Prediction and available scores]
    J --> K[Results page and report]
```

Until a trained model is connected, the API may validate an image
without making a prediction. It must report inference as unavailable
rather than returning a fabricated real/fake result.

### Planned model variants

1.  **RGB baseline:** a CNN such as ResNet18 processes the original
    image.
2.  **FFT baseline:** a CNN processes a normalized FFT magnitude
    representation.
3.  **RGB + FFT fusion:** combines learned features before
    classification.
4.  **Optional DWT variant:** tests wavelet subbands after the core
    baselines.

Verify actual tensor shapes and preprocessing conventions in code.

## Repository structure

This is a target structure, not a requirement to create empty
placeholders or rewrite working files.

``` text
project-root/
├── README.md
├── FRONTEND_DOCUMENTATION.md
├── .gitignore
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── api/routes/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── core/
│   ├── tests/
│   ├── .env.example
│   └── README.md
├── frontend/
│   ├── package.json
│   ├── .env.example
│   ├── README.md
│   └── src/
├── configs/
├── data/metadata/
├── scripts/
├── src/
│   ├── preprocessing/fft.py
│   ├── preprocessing/dwt.py
│   ├── datasets/
│   ├── models/rgb_model.py
│   ├── models/fft_model.py
│   ├── models/fusion_model.py
│   ├── training/
│   └── evaluation/
├── checkpoints/
└── experiments/
```

Keep datasets, uploaded images, environment files, and large model
checkpoints out of Git unless explicitly required.

## Development roadmap

### Phase 0 --- Specification and workspace setup

**Status: documentation revised; verify repository setup.**

-   Define image-only scope.
-   Keep `.gitignore` and environment examples accurate.
-   Remove video-focused instructions from the active plan.

### Phase 1 --- Multipage frontend

**Status: reported as substantially implemented; verify gaps.**

-   Home, Analyze, Results, History, and About pages.
-   Login/Register UI if required.
-   Image upload, preview, and client validation.
-   Demo mode with clear labels.
-   FFT visualization UI and working report download/print.
-   Create/update `FRONTEND_DOCUMENTATION.md`.
-   Run frontend tests and production build.

### Phase 2 --- FastAPI backend foundation

**Status: implemented and tested as the Phase A foundation.**

-   Configure FastAPI and Uvicorn.
-   Implement `GET /health`.
-   Implement `POST /api/v1/analyze` for a single image.
-   Validate actual image content, format, size, dimensions, and pixel
    count.
-   Add request-size protections and safe decoding.
-   Define stable request/response schemas.
-   Add centralized error handling and configurable CORS.
-   Return an explicit inference-unavailable response until a real model
    exists.
-   Add automated backend tests and `backend/README.md`.
-   Keep `/predict` only as a deprecated compatibility alias.
-   Do not return classification, confidence, calibrated probability, or
    model version until a verified checkpoint is loaded.
-   Keep Cloudflare R2 disabled and disconnected from user-image handling.

**Acceptance criteria:** the API starts; health works; valid images are
accepted; invalid, corrupted, unsupported, and oversized uploads are
rejected safely; tests verify response contracts. A trained model is not
required for this phase.

### Phase 3 --- Image dataset and preprocessing

**Status: implemented and tested.**

-   Select a permitted image dataset or prepare still images from an
    authorized research dataset.
-   Preserve source/identity metadata where available.
-   Split by source image; if frames come from videos, keep all frames
    from one source video in the same split.
-   Create reproducible metadata and preprocessing scripts.
-   Validate labels, duplicates, dimensions, and split integrity.
-   `backend/app/prepare_dataset.py` validates `data/raw/real` and
    `data/raw/fake`, then writes `train.csv`, `val.csv`, `test.csv`, and
    `report.json`.
-   RGB preprocessing returns configurable float32 CHW arrays at 224 x 224.
-   FFT preprocessing returns centered, stable, normalized log-magnitude maps.

### Phase 4 --- RGB baseline

**Status: implemented for CIFAKE; blocked for the mixed
FaceForensics++ export pending subset and source-group decisions.**

Phase 4 uses two independent RGB-only ResNet-18 tasks:

- FaceForensics++-derived still images: authentic (`real`, label `0`) versus
  validated manipulated (`fake`, label `1`) frames. A valid
  `frame-manifest.csv` with official source-video and manipulation metadata is
  required before training.
- CIFAKE: real images (`real`, label `0`) versus AI-generated images (`fake`,
  label `1`). Its held-out `external-test.csv` is never used for training or
  model selection.

Run preflight without training:

```powershell
.\.venv\Scripts\python.exe -m backend.training.rgb_baseline `
  --task cifake --manifest-dir data\metadata\cifake-image-v1 `
  --output-dir experiments\rgb-baseline --preflight-only
```

Train a task with pretrained ImageNet ResNet-18 weights:

```powershell
.\.venv\Scripts\python.exe -m backend.training.rgb_baseline `
  --task cifake --manifest-dir data\metadata\cifake-image-v1 `
  --output-dir experiments\rgb-baseline --epochs 5 --batch-size 16 --seed 42
```

The command saves an independent checkpoint, configuration, history, and
validation-selected test report under `experiments\rgb-baseline/`. Training
uses 224 x 224 RGB inputs, ImageNet normalization, AdamW, deterministic seeds,
and group-leakage/missing-image/duplicate preflight checks. The API remains
diagnostic-only until a separately reviewed checkpoint is intentionally wired
into inference. No FFT, fusion, video inference, or frontend changes are part
of this phase.

### Phase 5 --- FFT preprocessing and baseline

**Status: implemented for the CIFAKE task as a separate one-epoch CPU
baseline; not completed for the blocked face-manipulation task.**

The FFT input contract is deterministic and separate from diagnostic
visualizations: decode as RGB, convert to Pillow grayscale, resize to
224 x 224, compute `fft2` and `fftshift`, apply `log1p(abs(fft))`, normalize
each image to `[0, 1]`, and repeat the single channel three times for the
standard ResNet-18 input. It uses the same CIFAKE manifests, seed, optimizer,
split assignments, and metric definitions as the RGB baseline.

Reproducible commands:

```powershell
.\.venv\Scripts\python.exe -m backend.training.fft_baseline `
  --task cifake --manifest-dir data\metadata\cifake-image-v2 `
  --output-dir experiments\fft-baseline\cifake-image-v2 --preflight-only

.\.venv\Scripts\python.exe -m backend.training.fft_baseline `
  --task cifake --manifest-dir data\metadata\cifake-image-v2 `
  --output-dir experiments\fft-baseline\cifake-image-v2 `
  --epochs 1 --batch-size 32 --seed 42
```

Evaluation numbers are not claimed here unless they are regenerated with the
evaluation command below from committed checkpoints. CIFAKE external-test
data remains evaluation-only.

### Phase 6 --- RGB + FFT fusion

**Status: implemented for the CIFAKE task as a separate one-epoch CPU
baseline; not completed for the blocked face-manipulation task.**

The fusion model uses two ResNet-18 branches. One receives the normalized
224 x 224 RGB image and the other receives the deterministic FFT tensor from
Phase 5. Their 512-dimensional features are concatenated and passed to a
two-class linear head. A shared horizontal-flip decision keeps the two views
aligned during training.

```powershell
.\.venv\Scripts\python.exe -m backend.training.fusion_baseline `
  --task cifake --manifest-dir data\metadata\cifake-image-v2 `
  --output-dir experiments\fusion-baseline\cifake-image-v2 --preflight-only

.\.venv\Scripts\python.exe -m backend.training.fusion_baseline `
  --task cifake --manifest-dir data\metadata\cifake-image-v2 `
  --output-dir experiments\fusion-baseline\cifake-image-v2 `
  --epochs 1 --batch-size 32 --seed 42
```

Artifacts and comparisons are written under
`experiments\fusion-baseline\cifake-image-v2`. No accuracy claim is made
without a committed report produced by the evaluation command. The fusion
model is not connected to FastAPI.

### Phase 7 --- Optional DWT extension

**Status: optional future research.**

-   Add wavelet decomposition with PyWavelets.
-   Visualize approximation/detail subbands.
-   Test whether DWT contributes beyond RGB + FFT.

### Phase 8 --- Evaluation and robustness

**Status: implemented as a checkpoint-backed evaluation command.**

```powershell
.\.venv\Scripts\python.exe -m backend.training.evaluate `
  --eval-only --model rgb `
  --checkpoint experiments\rgb-baseline\cifake-image-v2\cifake-rgb-resnet18-best.pt `
  --manifest-dir data\metadata\cifake-image-v2 `
  --fft-input upsampled
```

The command reports point metrics, bootstrap 95% intervals, a mean/std pixel
logistic baseline, and JPEG/resize/blur/noise robustness results. Test sets
under 200 images are explicitly marked as not statistically meaningful.

-   Report accuracy, precision, recall, F1, ROC-AUC, and confusion
    matrix.
-   Test compression, resizing, blur, and other image transformations.
-   Evaluate external datasets where access terms permit.
-   Report results and limitations honestly.

### Phase 9 --- Real model/API/frontend integration

**Status: planned.**

-   Load a verified model checkpoint.
-   Connect inference to the image-analysis endpoint.
-   Return actual scores and model metadata.
-   Provide FFT visualizations from the validated image.
-   Replace demo data with real API responses in API mode.
-   Test the full upload-to-result workflow.

### Phase 10 --- Final validation and documentation

**Status: planned.**

-   Run backend/frontend tests and the production build.
-   Verify upload, errors, inference, and report generation.
-   Document model version, actual evaluation results, limitations, and
    reproduction steps.

## Dataset and data-leakage strategy

Potential sources such as FaceForensics++ and Celeb-DF originate as
video datasets. They may be used only if their access terms permit it
and still-image samples are prepared offline. The web application
remains image-only.

-   FaceForensics++: use the dataset's official distribution channel and record
    its licence and access terms in `dataset-source.json`.
-   Celeb-DF: https://github.com/yuezunli/celeb-deepfakeforensics
-   DFDC: https://www.kaggle.com/c/deepfake-detection-challenge

Before use, check dataset license, access rules, and permitted use. Do
not commit restricted datasets.

Leakage-prevention rules: - Split source images before creating derived
variants. - Keep frames from the same source video in the same split if
video-derived samples are used. - Where possible, isolate identities and
manipulation sources. - Keep the test set untouched until final
evaluation. - Record source IDs, labels, preprocessing version, and
split assignment. - Detect duplicates or near-duplicates where
practical.

## Evaluation plan

  Experiment                            Status
  ------------------------------------- ----------
  RGB-only                              Planned
  FFT-only                              Planned
  RGB + FFT fusion                      Planned
  RGB + FFT + optional DWT              Optional
  Robustness to image transformations   Planned

Do not populate metrics until experiments have run.

  Model         Accuracy   Precision   Recall    F1   ROC-AUC Notes
  ----------- ---------- ----------- -------- ----- --------- ------------------
  RGB-only           ---         ---      ---   ---       --- Not yet reported
  FFT-only           ---         ---      ---   ---       --- Not yet reported
  RGB + FFT          ---         ---      ---   ---       --- Not yet reported

## Frontend and API contract

The current backend contract is verified and image-only:

-   `GET /health` --- reports API availability and actual model status.
-   `POST /api/v1/analyze` --- accepts one image as multipart form data
    using the field name `file`.
-   `POST /predict` --- deprecated compatibility alias for
    `/api/v1/analyze`.

The current response always distinguishes diagnostics from inference:
`status` is `diagnostic_complete`, `inference_available` is `false`, and
`prediction`, `score`, and `model_version` are `null`. FFT, DWT, ELA, and
face-crop outputs are diagnostic visualizations and are not a deepfake
classification. The API rejects empty, corrupt, unsupported, oversized, and
dimensionally unsafe images. Uploaded originals are processed in memory and
are not stored by default.

Possible future fields include `analysis_id`, `filename`, `status`,
`prediction`, `score`, `score_type`, `checkpoint_task`, `label_semantics`,
`domain_warning`, `model_version`,
`processing_time_ms`, `branches.rgb`, `branches.fft`, `branches.fusion`,
`visualizations.fft_spectrum_url`, `created_at`, and `message`.

Use `null` or omit unavailable fields. Do not label a raw diagnostic value as a calibrated probability unless
calibration has been evaluated.

Example frontend environment:

``` env
VITE_DEMO_MODE=true
VITE_API_BASE_URL=http://localhost:8000
```

must be visibly labeled.

### Backend Integration & Diagnostic Scope

When running the frontend against the live Python FastAPI backend:

1. **Environment Variables**:
   In `frontend/.env`:
   ```env
   VITE_DEMO_MODE=false
   VITE_API_BASE_URL=http://localhost:8000
   VITE_ENABLE_AUTH=true
   VITE_APP_NAME="ImageForensics AI"
   ```

2. **Start the FastAPI Backend**:
   From the repository root with virtual environment activated:
   ```powershell
   python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
   ```
   Check health at `http://127.0.0.1:8000/health` and OpenAPI docs at `http://127.0.0.1:8000/docs`.

3. **Diagnostic-Only Scope**:
   > **Note on Model Output**: In this phase, the `/api/v1/analyze` endpoint produces **raw diagnostic feature decompositions** (face crop, 2D Fourier FFT magnitude spectrum, 4-quadrant Haar wavelet DWT subbands, spatial ELA heatmap, and radial spectral energy decay profiles). **No deepfake classification verdict or model confidence score is computed.** The frontend explicitly displays a **Diagnostic Only** badge, shows the diagnostic disclaimer banner, and suppresses classifier score cards.

## Installation and run commands

Commands are examples; verify them against the actual repository before
claiming they work.

### Python environment (Windows PowerShell)

``` powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

Install the root dependency file:

``` powershell
python -m pip install -r requirements.txt
```

### Run backend

Use the import path that matches the real layout. If
`backend/app/main.py` defines `app` and the repository root is the
working directory:

``` powershell
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

If implemented, test `http://127.0.0.1:8000/health` and inspect
`http://127.0.0.1:8000/docs`.

### Run frontend

``` powershell
cd frontend
npm install
npm run dev
```

### Tests and build

Run scripts defined by the actual project configuration, for example:

``` powershell
python -m pytest -q
npm test
npm run build
```

Do not claim a command passed unless it was executed. If a script is not
configured, document that fact.

## Testing and reproducibility

Record exact commands, dependency versions, test results, dataset/split
identifiers, preprocessing version, model configuration, checkpoint
version, and evaluation metrics where applicable.

A passing API test does not establish model accuracy. A successful
frontend build does not prove that the backend or model works.

## Limitations and responsible use

-   Predictions are not proof of authenticity or manipulation.
-   False positives and false negatives are possible.
-   Compression, resizing, sharpening, and camera pipelines affect
    frequency features.
-   Generalization to unseen manipulation methods must be evaluated.
-   Dataset biases can affect results.
-   Uploaded images should not be retained longer than necessary.
-   Backend validation is required even when frontend validation exists.
-   Do not use this experimental system as the sole basis for
    high-stakes accusations.

## Troubleshooting

-   **Frontend cannot reach API:** check API URL, backend process, and
    CORS origins.
-   **Image rejected:** check actual format, size, dimensions, and
    configured limits.
-   **Inference unavailable:** verify a trained checkpoint exists and
    loads; do not replace the missing model with fake results.
-   **CUDA unavailable:** check PyTorch build and driver compatibility;
    use CPU for small tests.
-   **Out-of-memory:** reduce batch size and avoid unnecessary image
    buffering.
-   **Tests fail:** reproduce and fix the failure before marking the
    feature complete.

## Next implementation step

Phase A backend hardening and diagnostic-only API behavior are implemented
and tested. Phase 3 image dataset validation and preprocessing are also
implemented and tested. The next step is Phase 4: define and implement an RGB baseline
only after a permitted dataset has been prepared and its manifests
reviewed. Do not claim detector accuracy before a real training run.

Cloudflare R2 has a separate read-only verification command:

```powershell
.\.venv\Scripts\python.exe -m backend.app.r2_verify
```

It requires `R2_ENABLED=true`, validates the endpoint and required variables,
checks bucket reachability, and lists no more than 20 names per dataset
prefix. It performs no write or delete operation.

The project's current research direction is single-image detection using
RGB and FFT features, with optional DWT after the core baselines. Video
inference and temporal modeling are not part of the current plan.
