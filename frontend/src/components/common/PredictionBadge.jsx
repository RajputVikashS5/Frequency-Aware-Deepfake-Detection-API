import React from 'react';
import { AlertTriangle, CheckCircle } from 'lucide-react';

export default function PredictionBadge({ isManipulated, isInconclusive = false, size = 'default' }) {
  const isLarge = size === 'large';

  if (isInconclusive) {
    return (
      <span className={`inline-flex items-center space-x-1.5 font-semibold rounded-md border ${
        isLarge
          ? 'px-3.5 py-1.5 text-sm bg-slate-800/60 text-slate-200 border-slate-600/80'
          : 'px-2.5 py-0.5 text-xs bg-slate-800/50 text-slate-200 border-slate-600/60'
      }`}>
        <span aria-hidden="true">?</span>
        <span>Inconclusive</span>
      </span>
    );
  }

  if (isManipulated) {
    return (
      <span
        className={`inline-flex items-center space-x-1.5 font-semibold rounded-md border ${
          isLarge
            ? 'px-3.5 py-1.5 text-sm bg-red-950/40 text-red-300 border-red-800/80 shadow-sm'
            : 'px-2.5 py-0.5 text-xs bg-red-950/30 text-red-300 border-red-900/60'
        }`}
      >
        <AlertTriangle className={isLarge ? 'w-4 h-4 text-red-400' : 'w-3 h-3 text-red-400'} />
        <span>Likely Manipulated</span>
      </span>
    );
  }

  return (
    <span
      className={`inline-flex items-center space-x-1.5 font-semibold rounded-md border ${
        isLarge
          ? 'px-3.5 py-1.5 text-sm bg-emerald-950/40 text-emerald-300 border-emerald-800/80 shadow-sm'
          : 'px-2.5 py-0.5 text-xs bg-emerald-950/30 text-emerald-300 border-emerald-900/60'
      }`}
    >
      <CheckCircle className={isLarge ? 'w-4 h-4 text-emerald-400' : 'w-3 h-3 text-emerald-400'} />
      <span>Likely Real</span>
    </span>
  );
}
