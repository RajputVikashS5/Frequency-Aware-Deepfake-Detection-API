# Diagnosis: “Almost every image is AI-generated”

Date: 2026-10-29

## Evidence collected before code changes

### Frontend mode and label path

- `frontend/src/config/appConfig.js` sets `isDemoMode` to
  `import.meta.env.VITE_DEMO_MODE !== 'false'`. Therefore the frontend is in
  demo mode unless the production build explicitly sets
  `VITE_DEMO_MODE=false`.
- `frontend/src/services/demoService.js` does not classify the image:
  `isManipulated` and `confidencePct` are `null`, `scores` is `null`, and the
  findings say that no classifier prediction was produced.
- `frontend/src/services/analysisService.js` uses the live API only when demo
  mode is disabled. In live mode it maps exactly
  `raw.prediction === 'likely_manipulated'` to `isManipulated=true`; every
  other prediction is treated as not manipulated. There is no inversion or
  default-to-manipulated branch.
- `frontend/src/components/common/PredictionBadge.jsx` displays
  “Likely Manipulated” only when its `isManipulated` prop is truthy; falsy
  values display “Likely Real”.
- `frontend/src/pages/ResultsPage.jsx` renders the classification card only
  when `analysis.inferenceAvailable` is true. Diagnostic records do not render
  a classifier badge.

Conclusion: demo mode can hide the real API, but the demo implementation does
not produce an “all fake” prediction. The UI needs a more prominent mode/model
indicator and a startup warning, but the observed all-fake classification must
come from a live checkpoint or another caller.

### Labels, scores, and threshold

- `backend/app/dataset.py` defines `LABELS = {"real": 0, "fake": 1}`.
- `backend/training/rgb_baseline.py` passes `row.label` directly as the
  cross-entropy target. Its metrics and evaluation code use
  `softmax(logits, dim=1)[:, 1]` as the fake score and classify scores at
  `0.5`.
- `backend/app/model_inference.py` also uses
  `softmax(model(image), dim=1)[0, 1]` and currently maps scores at `0.5` to
  `likely_manipulated` versus `likely_real`.
- The existing API string mapping is therefore consistent with the dataset
  mapping: class 1 is fake/manipulated and class 0 is real.

### Artifacts required for checkpoint evidence

This checkout contains no `*.pt` checkpoints and no `val.csv` or `test.csv`
manifests. Consequently, the following requested measurements could not be
computed without inventing results:

- RGB, FFT, and fusion validation/test prediction counts by class.
- Confusion matrices, ROC-AUC, mean scores by true class, and score
  histograms for each checkpoint.
- Resolution-specific fake fractions for real uploads or CIFAKE-derived
  synthetic probes.
- Logits and softmax scores for 20 random real uploads.

No accuracy, AUC, fake fraction, or calibration number is claimed in this
document.

## Root-cause assessment

The source code does not show a frontend inversion or demo heuristic that
would force every image to “likely manipulated.” The most supported current
hypothesis is an unverified model/domain issue: the API applies a fixed 0.5
threshold to a raw class-1 softmax score, while CIFAKE training images are
32x32 and arbitrary uploads may have very different resolution and image
statistics. This remains a hypothesis until a real checkpoint and manifests
are supplied or generated and evaluated. The API should therefore refuse
confident labels for CIFAKE-only checkpoints on high-resolution uploads and
for scores in an uncertainty band, while checkpoint metadata should carry
threshold and calibration parameters.

