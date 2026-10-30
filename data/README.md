# Image dataset preparation

Phase 3 supports still images only. Video upload, frame extraction, temporal
models, and video-level predictions are not part of this workflow.

## Expected raw layout

```text
data/raw/
├── real/
│   ├── real_001.jpg
│   └── ...
└── fake/
    ├── fake_001.png
    └── ...
```

For Phase B dataset versions, use separate directories:

```text
data/raw/faceforensicspp/
  real/
  fake/
  groups.csv
  dataset-source.json
data/raw/CIfake/
  real/
  fake/
  dataset-source.json
```

`dataset-source.json` records provenance, licence/access terms, intended use,
label definitions, whether the still images are video-derived, grouping
policy, and limitations. FaceForensics++ requires a `groups.csv` row for every
image so source videos cannot cross splits. CIFAKE uses one image per group
when no source identity metadata exists and records a warning.

Labels are explicit and fixed:

- `real` maps to label `0`
- `fake` maps to label `1`

Supported formats are JPEG, PNG, WEBP, BMP, TIFF, and TIF. Unsupported and
unreadable files are reported and excluded; they are never relabeled.

For source-aware splitting, provide an optional CSV such as
`data/groups.csv` with `path,group_id` columns. Paths are relative to the
dataset root, for example `real/person-01.png,person-01`. Images with the
same group ID cannot cross train, validation, and test splits.

## Preparation

From the repository root in Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m backend.app.prepare_dataset `
  --input data\raw `
  --output data\metadata `
  --seed 42
```

With source groups:

```powershell
.\.venv\Scripts\python.exe -m backend.app.prepare_dataset `
  --input data\raw `
  --groups-file data\groups.csv `
  --output data\metadata `
  --seed 42
```

The command creates `train.csv`, `val.csv`, `test.csv`, and `report.json`.
It does not download data or create sample images.

FaceForensics++-derived images and CIFAKE are prepared as separate versioned
datasets. Do not combine them implicitly. The exact offline commands and
their image-only boundary are documented in
[`backend/README.md`](../backend/README.md). Model training begins only
after the generated manifests, provenance, exclusions, and split-integrity
reports have been reviewed.

Downloaded datasets, generated metadata reports, and evaluation outputs are
local-only artifacts and are excluded from Git. Keep reproducible preparation
commands and provenance files in the repository instead of committing dataset
images or generated report dumps.

## Preprocessing settings

`backend.app.preprocessing.preprocess_rgb` converts images to RGB, resizes to
224 x 224 by default, and returns a float32 NumPy array with shape
`(3, 224, 224)`. Values are scaled to `[0, 1]` when normalization is disabled.
The default ImageNet mean and standard deviation are configurable and are
applied consistently when enabled.

`backend.app.frequency.fft_log_magnitude` computes a centered 2D FFT and
`log1p` magnitude. Its default output is a finite float32 array with shape
`(H, W)` and values normalized to `[0, 1]`. The FFT is a diagnostic
representation; it does not independently prove manipulation.

## Access and licensing

Obtain datasets only from sources whose license and access terms permit the
intended research use. Do not commit raw images, restricted datasets,
generated manifests, or model artifacts to Git.
