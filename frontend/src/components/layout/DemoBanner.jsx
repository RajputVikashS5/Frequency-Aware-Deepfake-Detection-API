import React from 'react';
import { AlertTriangle, Sparkles } from 'lucide-react';
import { appConfig } from '../../config/appConfig';

export default function DemoBanner({ isDiagnostic = false, message = null }) {
  const shouldShow = appConfig.isDemoMode || isDiagnostic;

  if (!shouldShow) return null;

  const defaultText = appConfig.isDemoMode
    ? 'DEMO MODE – Results are generated locally for prototype validation. No trained classifier is used.'
    : 'DIAGNOSTIC INSPECTION – Multi-modal frequency and spatial decomposition. No trained classifier verdict is generated.';

  return (
    <aside
      role="status"
      aria-live="polite"
      className="bg-card-subtle border-b border-border text-xs text-amber-300 py-2 px-4 text-center no-print transition-colors"
    >
      <div className="max-w-7xl mx-auto flex items-center justify-center space-x-2 flex-wrap">
        <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse shrink-0" />
        <span className="font-semibold text-amber-300 uppercase tracking-wider font-mono text-[11px]">
          {isDiagnostic && !appConfig.isDemoMode ? 'Diagnostic Mode:' : 'Demo Mode:'}
        </span>
        <span className="text-slate-300 text-[11px]">
          {message || defaultText}
        </span>
      </div>
    </aside>
  );
}
