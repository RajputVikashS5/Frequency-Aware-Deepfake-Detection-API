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
FaceForensics++ CSV findings are documented in
[`DATASET_INVENTORY_AND_INTEGRATION.md`](../DATASET_INVENTORY_AND_INTEGRATION.md).

## Offline image-only dataset preparation

The deployed FastAPI product remains image-only. FaceForensics++ MP4 files are
handled only by offline commands after explicit bounded download; no video
upload endpoint, video API, timeline, temporal model, or video prediction is
added.

Inventory R2 without downloading objects:

```powershell
.\.venv\Scripts\python.exe -m backend.app.inventory_faceforensicspp `
  --dataset faceforensicspp --max-objects 1000
.\.venv\Scripts\python.exe -m backend.app.inventory_faceforensicspp `
  --dataset cifake --max-objects 1000
```

Inspect bounded CSV metadata previews without assuming a schema:

```powershell
.\.venv\Scripts\python.exe -m backend.app.inventory_faceforensicspp `
  --dataset faceforensicspp --inspect-csv data\faceforensicspp\csv\metadata.csv `
  --preview-rows 5 --max-objects 1
# For an R2 CSV key, use --csv-key faceforensics++/csv/<official-file>.csv
```

Download selected FaceForensics++ videos only:

```powershell
.\.venv\Scripts\python.exe -m backend.app.download_faceforensicspp_videos `
  --key faceforensics++/original/example.mp4 --max-videos 1 `
  --output data\downloads\faceforensicspp
```

Extract bounded, evenly spaced local frames (not through FastAPI):

```powershell
.\.venv\Scripts\python.exe -m backend.app.extract_faceforensicspp_frames `
  --input data\downloads\faceforensicspp\original\example.mp4 `
  --output data\frames\example --samples 8 --margin 0.05
```

Create the FaceForensics++-derived image dataset. The mapping CSV must contain
official manipulated-key, source/original-video-ID, and manipulation-type
columns; filename inference is rejected:

```powershell
.\.venv\Scripts\python.exe -m backend.app.prepare_faceforensicspp_images `
  --videos data\downloads\faceforensicspp `
  --mapping-csv data\faceforensicspp\csv\mapping.csv `
  --source-metadata data\faceforensicspp-image-dataset-template\dataset-source.json `
  --output data\raw\faceforensicspp-images-v1 --samples 8 --margin 0.05
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
  --input data\raw\faceforensicspp-images-v1 `
  --output data\metadata\faceforensicspp-images-v1 `
  --dataset faceforensicspp --seed 42
```

Review generated manifests, provenance, exclusions, and split-integrity
reports before any model training begins. No training, metrics, predictions,
or checkpoints are created by these commands.

## Phase 4 RGB baseline

The RGB baseline has independent runs for FaceForensics++-derived still images and
CIFAKE. It uses pretrained ImageNet ResNet-18 weights, 224 x 224 RGB inputs,
ImageNet normalization, AdamW, deterministic seeds, validation checkpoint
selection, and final test evaluation. Preflight checks missing/corrupt images,
duplicate records, and source-group leakage.

```powershell
.\.venv\Scripts\python.exe -m backend.training.rgb_baseline `
  --task cifake --manifest-dir data\metadata\cifake-image-v1 `
  --output-dir experiments\rgb-baseline --preflight-only

.\.venv\Scripts\python.exe -m backend.training.rgb_baseline `
  --task cifake --manifest-dir data\metadata\cifake-image-v1 `
  --output-dir experiments\rgb-baseline --epochs 5 --batch-size 16 --seed 42

.\.venv\Scripts\python.exe -m backend.training.rgb_baseline `
  --task faceforensicspp --manifest-dir data\metadata\faceforensicspp-images-v1 `
  --source-frame-manifest data\raw\faceforensicspp-images-v1\frame-manifest.csv `
  --output-dir experiments\rgb-baseline --epochs 5 --batch-size 16 --seed 42
```

FaceForensics++ training requires the official source-video/manipulation mapping
from `frame-manifest.csv`; filename-only inference is rejected. CIFAKE's
`external-test.csv` is evaluation-only and is never used for training or
model selection. Generated checkpoints, configurations, histories, and reports
remain ignored artifacts. Review dataset provenance and split-integrity reports
before using metrics.

## Phase 5 FFT-only baseline

The FFT baseline is implemented separately from the RGB baseline and does not
change FastAPI or frontend behavior. Its input contract is:

```text
RGB decode -> Pillow grayscale -> resize 224x224 -> fft2 -> fftshift
-> log1p(abs(fft)) -> per-image min-max [0, 1] -> repeat to 3 channels
```

It uses the same CIFAKE v2 manifests, label mapping, seed, optimizer, split
assignments, validation checkpoint selection, and metric definitions as the
RGB run. Diagnostic FFT images are not used as a substitute for model input.

```powershell
.\.venv\Scripts\python.exe -m backend.training.fft_baseline `
  --task cifake --manifest-dir data\metadata\cifake-image-v2 `
  --output-dir experiments\fft-baseline\cifake-image-v2 --preflight-only

.\.venv\Scripts\python.exe -m backend.training.fft_baseline `
  --task cifake --manifest-dir data\metadata\cifake-image-v2 `
  --output-dir experiments\fft-baseline\cifake-image-v2 `
  --epochs 1 --batch-size 32 --seed 42
```

The report, history, configuration, checkpoint, and RGB-versus-FFT
comparison are written under `experiments\fft-baseline\cifake-image-v2`.
The observed one-epoch internal-test accuracies were 93.50% for RGB and
85.45% for FFT on the identical CIFAKE split. FaceForensics++-derived training
remains blocked until its actual dataset identity and official source-video
mappings are verified.

## Phase 6 RGB + FFT fusion

The fusion baseline uses two ResNet-18 branches: one for normalized RGB and
one for the Phase 5 FFT tensor. The two 512-dimensional feature vectors are
concatenated into a two-class linear head. RGB and FFT views receive the same
horizontal-flip decision so they remain aligned.

```powershell
.\.venv\Scripts\python.exe -m backend.training.fusion_baseline `
  --task cifake --manifest-dir data\metadata\cifake-image-v2 `
  --output-dir experiments\fusion-baseline\cifake-image-v2 --preflight-only

.\.venv\Scripts\python.exe -m backend.training.fusion_baseline `
  --task cifake --manifest-dir data\metadata\cifake-image-v2 `
  --output-dir experiments\fusion-baseline\cifake-image-v2 `
  --epochs 1 --batch-size 32 --seed 42
```

The one-epoch internal-test accuracies were 93.50% RGB, 85.45% FFT, and
93.21% fusion on the same split. See the fusion experiment directory for the
checkpoint, configuration, history, report, and comparison report. This
model remains training-only and is not connected to the API.

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

## RGB baseline training and inference

After an approved dataset's manifests pass validation, train a baseline locally:

```powershell
.\.venv\Scripts\python.exe -m backend.training.rgb_baseline `
  --task cifake `
  --manifest-dir data\metadata\cifake-image-v2 `
  --output-dir experiments\rgb-cifake-v1 `
  --epochs 5 --batch-size 32 --no-pretrained
```

Review the generated report before enabling inference. To load only the selected
checkpoint, set `MODEL_CHECKPOINT_PATH` and `MODEL_VERSION` in `.env` and restart
the API. The endpoint reports `inference_complete` only when this checkpoint loads
successfully. Its `score` is an **uncalibrated** RGB-baseline probability.

Run the read-only connectivity and dataset-prefix check after configuring
`.env`:

```powershell
.\.venv\Scripts\python.exe -m backend.app.r2_verify
```

The verifier keeps the bucket name separate from object keys, checks
`head_bucket`, and lists at most 20 object names under the configured
`R2_FACEFORENSICSPP_PREFIX` and `R2_CIFAKE_PREFIX`. Select one dataset or both:

```powershell
.\.venv\Scripts\python.exe -m backend.app.r2_verify --dataset faceforensicspp
.\.venv\Scripts\python.exe -m backend.app.r2_verify --dataset cifake
.\.venv\Scripts\python.exe -m backend.app.r2_verify --all-datasets
```

For the configured `deepfake` bucket, the all-datasets check is:

```powershell
.\.venv\Scripts\python.exe -m backend.app.r2_verify --all-datasets
```

Expected successful output begins with:

```text
faceforensics++/: accessible
CIfake/: accessible
```

The controlled sample command is explicit and capped at 5,000 images per label:

```powershell
.\.venv\Scripts\python.exe -m backend.app.fetch_dataset_sample `
  --dataset cifake --per-label 10 `
  --output data\sample\cifake
```

Local preparation requires `dataset-source.json`; FaceForensics++ also
requires complete `groups.csv` mappings. CIFAKE may fall back to one group per
image only when that limitation is recorded in the report. Generated artifact
uploads are disabled unless `prepare_dataset` receives `--upload-r2`; uploads
are limited to `manifests/<dataset-version>/` and never include user uploads
or raw datasets.
