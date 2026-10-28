# Dataset inventory and RGB + FFT integration

## Current R2 layout

The configured prefixes are read from `R2_FACEFORENSICSPP_PREFIX` and
`R2_CIFAKE_PREFIX` (defaults: `faceforensics++/` and `CIfake/`). The bucket name is
kept separate from object keys. The inventory never downloads image or video
objects.

The observed listing before this implementation was:

- FaceForensics++: `7,010` objects (`7,000` MP4 and `10` CSV objects).
- CIFAKE: the prior `10,000`-object scan was incomplete and must not be used as
  a dataset total.

These are historical observations, not a claim that the current bucket is
unchanged or that CIFAKE is complete.

The live inventory performed during this implementation completed both
prefixes. Current observed counts were:

- FaceForensics++: `7,010` objects, `7,000` MP4, `10` CSV, `1,000` original and
  `6,000` manipulated videos; no unknown objects.
- CIFAKE: `23,550` objects, `23,549` JPG and one extensionless object.
  Recognized images were train `4,515` real / `4,516` fake and test `10,000`
  real / `4,518` fake. One object was unclassified and the class totals
  reconciled to the recognized image count.

These counts are timestamped by the live run, not persisted as a dataset
version. Re-run the command before using them for training.

## Pagination and confidence

`backend.app.inventory_faceforensicspp` calls `list_objects_v2` with continuation
tokens and a bounded `MaxKeys`. A report has:

- `completed: true` when the service reported the final page.
- `truncated_by_limit: true` only when the configured limit stopped a response
  that still had more pages.
- `warnings` for listing failures, malformed pagination, or partial results.

An exact limit-sized final page is therefore complete; an exact limit-sized
prefix with `IsTruncated=true` is partial. Transient listing failures are
retried twice with bounded backoff and are reported rather than hidden.

## CIFAKE classification

Keys are parsed case-insensitively by locating a `train` or `test` path
component, followed anywhere later by `real` or `fake`. This supports the
verified common layout:

```text
CIfake/train/REAL/<image>
CIfake/train/FAKE/<image>
CIfake/test/REAL/<image>
CIfake/test/FAKE/<image>
```

The scanner does not classify extensionless objects or unknown layouts. It
reports `unknown_or_unclassified_objects`, representative keys for each
partition/class, recognized image totals, and a reconciliation flag.

Run a complete scan only with a limit above the expected object count:

```powershell
.\.venv\Scripts\python.exe -m backend.app.inventory_faceforensicspp `
  --dataset cifake --max-objects 1000000
```

To produce a deduplicated object-key manifest without downloading image bytes:

```powershell
.\.venv\Scripts\python.exe -m backend.app.inventory_faceforensicspp `
  --dataset cifake --max-objects 1000000 `
  --manifest-output data\metadata\cifake-r2-image-manifest.csv
```

The manifest fields are `dataset`, `object_key`, `media_type`, `label`,
`manipulation_type`, `partition`, `source_video_id`, and `metadata_source`.
It is a source/object manifest for the existing local preparation pipeline; it
does not replace the validated RGB preprocessing or FFT feature code.

## FaceForensics++ metadata

The inventory counts CSV objects and provides bounded CSV inspection. CSV
headers and representative rows are preserved without assigning meaning to
unknown columns:

```powershell
.\.venv\Scripts\python.exe -m backend.app.inventory_faceforensicspp `
  --dataset faceforensicspp --max-objects 1000000 `
  --csv-key faceforensics++/csv/<metadata-file>.csv --preview-rows 10
```

The ten current CSV objects use the verified columns `File Path` and `Label`
(plus frame/video properties) except `Mean_Data.csv`, which is an aggregate
statistics table. `FF++_Metadata_Shuffled.csv` includes both original `REAL`
and manipulated `FAKE` rows. The parser maps only an exact recognized
`File Path`/`Label` shape, normalizes labels case-insensitively, preserves
object keys and metadata source, and reports unmatched entries, duplicate
entries, ambiguous labels, and videos without metadata. It does not treat the
aggregate CSV as per-video metadata.

Use the official mapping CSV with `prepare_faceforensicspp_images`; it must expose
manipulated-video key, source/original-video identifier, and manipulation-type
columns. The existing command rejects missing or ambiguous mappings instead of
inferring a label from a filename or folder:

```powershell
.\.venv\Scripts\python.exe -m backend.app.prepare_faceforensicspp_images `
  --videos data\downloads\faceforensicspp `
  --mapping-csv data\faceforensicspp\csv\mapping.csv `
  --source-metadata data\faceforensicspp-image-dataset-template\dataset-source.json `
  --output data\raw\faceforensicspp-images-v1 --samples 8 --margin 0.05
```

Original videos remain `real`; mapped manipulated videos are `fake`, with
source-video group IDs retained so frame splits cannot leak across videos.
Unknown, missing, or ambiguous mappings are excluded and written to
`exclusions.csv`.

## Tests and local preparation

Run the complete offline suite without cloud credentials:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Prepare a bounded CIFAKE sample after selecting/download only the desired
objects:

```powershell
.\.venv\Scripts\python.exe -m backend.app.fetch_dataset_sample `
  --dataset cifake --partition train --per-label 10 `
  --output data\downloads\cifake
.\.venv\Scripts\python.exe -m backend.app.prepare_cifake_images `
  --input data\downloads\cifake `
  --output data\metadata\cifake-image-v1 `
  --source-metadata data\cifake-image-dataset-template\dataset-source.json `
  --seed 42
```

The CIFAKE `test` partition is emitted as `external-test.csv` and marked
evaluation-only. It is not used for training, calibration, or model selection.
FaceForensics++ frame extraction is intentionally bounded:

```powershell
.\.venv\Scripts\python.exe -m backend.app.extract_faceforensicspp_frames `
  --input data\downloads\faceforensicspp\original\example.mp4 `
  --output data\frames\example --samples 8 --margin 0.05
```

No live R2 inventory was run as part of the offline test suite. A live run
requires the existing `.env` configuration and must be treated as the source
of current counts. Do not copy credentials into command output or reports.
