# Backend

The FastAPI service accepts individual images through `POST /api/v1/analyze`
and exposes `/health`. Its response is diagnostic only and does not represent
a trained or calibrated detector. `/predict` remains only as a deprecated
compatibility alias.

Run the API from the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload `
  --host 127.0.0.1 --port 8000
```

Prepare an image dataset:

```powershell
.\.venv\Scripts\python.exe -m backend.app.prepare_dataset `
  --input data\raw --output data\metadata --seed 42
```

Run the backend and Phase A tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The dataset command never downloads data, fabricates images, or silently
changes labels. See [`data/README.md`](../data/README.md) for the expected
layout and licensing cautions.

The complete inventory, verified live counts, object-manifest format, and
ForgeryNet CSV findings are documented in
[`DATASET_INVENTORY_AND_INTEGRATION.md`](../DATASET_INVENTORY_AND_INTEGRATION.md).

## Offline image-only dataset preparation

The deployed FastAPI product remains image-only. ForgeryNet MP4 files are
handled only by offline commands after explicit bounded download; no video
upload endpoint, video API, timeline, temporal model, or video prediction is
added.

Inventory R2 without downloading objects:

```powershell
.\.venv\Scripts\python.exe -m backend.app.inventory_forgerynet `
  --dataset forgerynet --max-objects 1000
.\.venv\Scripts\python.exe -m backend.app.inventory_forgerynet `
  --dataset cifake --max-objects 1000
```

Inspect bounded CSV metadata previews without assuming a schema:

```powershell
.\.venv\Scripts\python.exe -m backend.app.inventory_forgerynet `
  --dataset forgerynet --inspect-csv data\forgerynet\csv\metadata.csv `
  --preview-rows 5 --max-objects 1
# For an R2 CSV key, use --csv-key forgerynet/csv/<official-file>.csv
```

Download selected ForgeryNet videos only:

```powershell
.\.venv\Scripts\python.exe -m backend.app.download_forgerynet_videos `
  --key forgerynet/original/example.mp4 --max-videos 1 `
  --output data\downloads\forgerynet
```

Extract bounded, evenly spaced local frames (not through FastAPI):

```powershell
.\.venv\Scripts\python.exe -m backend.app.extract_forgerynet_frames `
  --input data\downloads\forgerynet\original\example.mp4 `
  --output data\frames\example --samples 8 --margin 0.05
```

Create the ForgeryNet-derived image dataset. The mapping CSV must contain
official manipulated-key, source/original-video-ID, and manipulation-type
columns; filename inference is rejected:

```powershell
.\.venv\Scripts\python.exe -m backend.app.prepare_forgerynet_images `
  --videos data\downloads\forgerynet `
  --mapping-csv data\forgerynet\csv\mapping.csv `
  --source-metadata data\forgerynet-image-dataset-template\dataset-source.json `
  --output data\raw\forgerynet-images-v1 --samples 8 --margin 0.05
```

Bounded CIFAKE image download is performed by the explicit R2 sample command
after selecting keys from the inventory; the local preparation command keeps
`train` separate from the held-out `test` partition:

```powershell
.\.venv\Scripts\python.exe -m backend.app.fetch_dataset_sample `
  --dataset cifake --partition train --per-label 10 --output data\downloads\cifake
.\.venv\Scripts\python.exe -m backend.app.fetch_dataset_sample `
  --dataset cifake --partition test --per-label 10 --output data\downloads\cifake
.\.venv\Scripts\python.exe -m backend.app.prepare_cifake_images `
  --input data\downloads\cifake --output data\metadata\cifake-image-v1 `
  --source-metadata data\cifake-image-dataset-template\dataset-source.json `
  --seed 42
```

The CIFAKE preparation command creates train/validation/test manifests from
training images only and a separate `external-test.csv` marked
`external_evaluation_only=true`. External-test data must never be used for
training, calibration, threshold selection, augmentation, or model selection.
The existing generic image manifest command remains available:

```powershell
.\.venv\Scripts\python.exe -m backend.app.prepare_dataset `
  --input data\raw\forgerynet-images-v1 `
  --output data\metadata\forgerynet-images-v1 `
  --dataset forgerynet --seed 42
```

Review generated manifests, provenance, exclusions, and split-integrity
reports before any model training begins. No training, metrics, predictions,
or checkpoints are created by these commands.

## API contract

`POST /api/v1/analyze` accepts one multipart image field named `file`.
Supported content types and actual formats are JPEG, PNG, WEBP, and BMP.
Responses contain `status: "diagnostic_complete"`,
`inference_available: false`, `prediction: null`, `score: null`, and
`model_version: null`. FFT, DWT, ELA, and face-crop outputs are diagnostic
visualizations only.

Validation defaults:

- Maximum upload: 10 MiB
- Maximum width and height: 8192 pixels
- Maximum total pixels: 40,000,000
- Allowed frontend origins: localhost and 127.0.0.1 on port 5173

Override these with environment variables documented in [`.env.example`](../.env.example).
Uploaded originals are processed in memory and are not written to disk or R2.

## Cloudflare R2

R2 settings are present for future dataset/checkpoint artifact storage only.
`R2_ENABLED=false` by default, and the isolated R2 client is not connected to
user image handling. No credentials are included and Phase A performs no R2
uploads.

Run the read-only connectivity and dataset-prefix check after configuring
`.env`:

```powershell
.\.venv\Scripts\python.exe -m backend.app.r2_verify
```

The verifier keeps the bucket name separate from object keys, checks
`head_bucket`, and lists at most 20 object names under the configured
`R2_FORGERYNET_PREFIX` and `R2_CIFAKE_PREFIX`. Select one dataset or both:

```powershell
.\.venv\Scripts\python.exe -m backend.app.r2_verify --dataset forgerynet
.\.venv\Scripts\python.exe -m backend.app.r2_verify --dataset cifake
.\.venv\Scripts\python.exe -m backend.app.r2_verify --all-datasets
```

For the configured `deepfake` bucket, the all-datasets check is:

```powershell
.\.venv\Scripts\python.exe -m backend.app.r2_verify --all-datasets
```

Expected successful output begins with:

```text
forgerynet/: accessible
CIfake/: accessible
```

The controlled sample command is explicit and capped at ten images per label:

```powershell
.\.venv\Scripts\python.exe -m backend.app.fetch_dataset_sample `
  --dataset forgerynet --per-label 10 `
  --output data\sample\forgerynet
```

Local preparation requires `dataset-source.json`; ForgeryNet also
requires complete `groups.csv` mappings. CIFAKE may fall back to one group per
image only when that limitation is recorded in the report. Generated artifact
uploads are disabled unless `prepare_dataset` receives `--upload-r2`; uploads
are limited to `manifests/<dataset-version>/` and never include user uploads
or raw datasets.
