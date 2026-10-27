# CIFAKE recovery and preparation

## Root cause of the earlier failure

The sample fetcher previously requested only the first R2 listing page. R2
returned keys in an order where the first ten eligible images were all under
`FAKE`, so no `REAL` images were downloaded. It also rejected any non-empty
output directory before the second partition could be added.

The preparation command then received `data\downloads\cifake`, which contained
only `train\fake`; the separately downloaded test sample was under
`data\downloads\cifake_test`. Consequently, the required `test` directory was
absent.

## Canonical structure

Both partitions belong under one root:

```text
data/downloads/cifake/
  train/real/
  train/fake/
  test/real/
  test/fake/
  sample-manifest.json
  recovery-report.json        # recovery only
```

Labels are obtained from the verified R2 object-key path, case-insensitively.
Unknown paths are never assigned a label.

## Sample manifest

`sample-manifest.json` contains `dataset`, the configured dataset `prefix`,
`per_label_limit`, `full_dataset_downloaded: false`, counts, warnings, and
objects with:

```json
{
  "key": "CIfake/train/REAL/example.jpg",
  "partition": "train",
  "local_path": "data\\downloads\\cifake\\train\\real\\00.jpg",
  "label_name": "real",
  "label": 0,
  "sha256": "...",
  "size_bytes": 12345,
  "width": 256,
  "height": 256,
  "format": "JPEG",
  "status": "downloaded"
}
```

The fetcher paginates all objects under the requested partition before
selecting candidates. Repeated fetches reuse source keys already recorded and
choose the next unused local filename. Existing files are not deleted.

## Recovery

Recovery reads existing manifests and verifies each referenced local image.
It preserves the original sample roots, copies verified files into the
canonical root, avoids source-key and filename collisions, and writes
`recovery-report.json` with `reused`, `downloaded`, `skipped`, `invalid`, and
`missing` entries.

## Validation

Validation does not download, copy, move, or relabel anything:

```powershell
.\.venv\Scripts\python.exe -m backend.app.prepare_cifake_images `
  --input data\downloads\cifake --validate-only
```

It reports image totals, partition/class counts, corrupt files, missing
combinations, duplicate content, manifest entries without files, files without
manifest entries, and whether the manifest identifies the dataset as a
sample. Exit code `0` requires both partitions/classes and readable images.

## Recovery and download workflow

Recover the two existing samples first:

```powershell
.\.venv\Scripts\python.exe -m backend.app.fetch_dataset_sample `
  --output data\downloads\cifake `
  --recover-from data\downloads\cifake `
  --recover-from data\downloads\cifake_test
```

Then fetch missing classes into the same root. These commands do not require
`--force` and do not overwrite existing source-key records:

```powershell
.\.venv\Scripts\python.exe -m backend.app.fetch_dataset_sample `
  --dataset cifake --partition train --per-label 10 `
  --output data\downloads\cifake

.\.venv\Scripts\python.exe -m backend.app.fetch_dataset_sample `
  --dataset cifake --partition test --per-label 10 `
  --output data\downloads\cifake
```

Validate before preparing:

```powershell
.\.venv\Scripts\python.exe -m backend.app.prepare_cifake_images `
  --input data\downloads\cifake --validate-only
```

Prepare the existing RGB-compatible manifests:

```powershell
.\.venv\Scripts\python.exe -m backend.app.prepare_cifake_images `
  --input data\downloads\cifake `
  --output data\metadata\cifake-image-v1 `
  --source-metadata data\cifake-image-dataset-template\dataset-source.json `
  --seed 42
```

The preparation command uses only `train` for train/validation/test splits and
keeps the original `test` partition as `external-test.csv`. It does not claim
that a bounded sample is the complete CIFAKE dataset.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Normal tests use mocked R2 clients and do not require cloud credentials.
