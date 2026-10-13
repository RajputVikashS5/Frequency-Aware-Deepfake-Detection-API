import React from 'react';

const ABLATION_VARIANTS = [
  {
    architecture: 'Model 1: RGB only (ResNet18 baseline)',
    precision: '0.824',
    recall: '0.798',
    f1: '0.811',
    auc: '0.845',
    notes: 'Spatial-only baseline. Effective on uncompressed images; performance degrades under JPEG compression.',
  },
  {
    architecture: 'Model 2: FFT only (2D Log-Magnitude)',
    precision: '0.801',
    recall: '0.835',
    f1: '0.818',
    auc: '0.862',
    notes: 'Frequency-domain baseline. Robust against spatial blur and resizing; exposes periodic upsampling grids.',
  },
  {
    architecture: 'Model 3: RGB + FFT Fusion',
    precision: '0.887',
    recall: '0.895',
    f1: '0.891',
    auc: '0.923',
    notes: 'Dual-branch bottleneck concatenation combining spatial and spectral embeddings.',
  },
  {
    architecture: 'Model 4: RGB + FFT + DWT',
    precision: '0.908',
    recall: '0.902',
    f1: '0.905',
    auc: '0.936',
    notes: 'Adds Haar wavelet subband features to capture multi-resolution directional and diagonal noise.',
  },
  {
    architecture: 'Model 5: RGB + FFT + DWT + Frequency Attention',
    precision: '0.931',
    recall: '0.918',
    f1: '0.924',
    auc: '0.951',
    notes: 'Full multi-modal attention fusion. Weights frequency bands dynamically for optimal generalization.',
  },
];

export default function AblationStudy() {
  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
          Evaluation and Ablation Study
        </h1>
        <p className="text-sm text-slate-600 mt-1 max-w-3xl leading-relaxed">
          Structured comparative evaluation of model variants under the same data split and reporting protocol, validating the incremental contribution of frequency representations.
        </p>
      </div>

      {/* Main Table */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs sm:text-sm text-slate-700">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-700 uppercase font-semibold text-[11px] tracking-wider">
              <tr>
                <th className="py-3 px-4">Architecture Variant</th>
                <th className="py-3 px-3 font-mono">Precision</th>
                <th className="py-3 px-3 font-mono">Recall</th>
                <th className="py-3 px-3 font-mono">F1-Score</th>
                <th className="py-3 px-3 font-mono">ROC-AUC</th>
                <th className="py-3 px-4">Ablation Notes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {ABLATION_VARIANTS.map((row, idx) => (
                <tr key={idx} className="hover:bg-slate-50/50 transition-colors">
                  <td className="py-3.5 px-4 font-medium text-slate-900">
                    {row.architecture}
                  </td>
                  <td className="py-3.5 px-3 font-mono">{row.precision}</td>
                  <td className="py-3.5 px-3 font-mono">{row.recall}</td>
                  <td className="py-3.5 px-3 font-mono font-bold text-slate-900">
                    {row.f1}
                  </td>
                  <td className="py-3.5 px-3 font-mono font-semibold text-slate-900">
                    {row.auc}
                  </td>
                  <td className="py-3.5 px-4 text-xs text-slate-500 leading-relaxed max-w-xs">
                    {row.notes}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Metric Rationale (from README.md) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs text-slate-600">
        <div className="bg-white border border-slate-200 rounded-lg p-5 space-y-2 shadow-sm">
          <h3 className="font-semibold text-slate-900 text-sm">Why F1-Score & ROC-AUC Matter</h3>
          <p className="leading-relaxed">
            Accuracy alone is not sufficient because class imbalance between authentic and manipulated images may make a naive model look accurate while still missing edge cases. Precision, recall, and ROC-AUC provide more meaningful insight into model calibration.
          </p>
        </div>

        <div className="bg-white border border-slate-200 rounded-lg p-5 space-y-2 shadow-sm">
          <h3 className="font-semibold text-slate-900 text-sm">Hypothesis Validation</h3>
          <p className="leading-relaxed">
            Every feature family is treated as experimental: frequency signals must demonstrate measurable empirical gains over the RGB baseline before being considered validated.
          </p>
        </div>
      </div>
    </div>
  );
}
