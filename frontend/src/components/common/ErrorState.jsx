import React from 'react';
import { AlertCircle, RotateCcw } from 'lucide-react';

export default function ErrorState({ message, onRetry }) {
  return (
    <div className="bg-red-950/20 border border-red-900/50 rounded-xl p-8 text-center flex flex-col items-center justify-center space-y-3">
      <div className="p-2.5 bg-red-900/30 rounded-lg text-red-400">
        <AlertCircle className="w-6 h-6" />
      </div>
      <h3 className="font-bold text-red-300 text-sm">Operation Failed</h3>
      <p className="text-xs text-slate-300 max-w-md leading-relaxed">{message || 'An unexpected error occurred.'}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-2 inline-flex items-center space-x-1.5 px-3.5 py-1.5 text-xs font-semibold text-slate-100 bg-card hover:bg-card-hover border border-border rounded-md transition-colors"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Retry</span>
        </button>
      )}
    </div>
  );
}
