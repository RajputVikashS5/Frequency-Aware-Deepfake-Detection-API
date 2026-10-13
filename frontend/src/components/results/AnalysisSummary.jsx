import React from 'react';
import { Info, FileText } from 'lucide-react';

export default function AnalysisSummary({ findings, modelVersion }) {
  if (!findings || findings.length === 0) return null;

  return (
    <div className="bg-card rounded-xl border border-border p-5 space-y-3">
      <div className="flex items-center space-x-2">
        <Info className="w-4 h-4 text-accent-cyan" />
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200 font-mono">
          Diagnostic Evidence Summary
        </h4>
      </div>

      <ul className="space-y-2 text-xs text-slate-300 leading-relaxed">
        {findings.map((finding, idx) => (
          <li key={idx} className="flex items-start space-x-2">
            <span className="text-accent-cyan font-bold">•</span>
            <span>{finding}</span>
          </li>
        ))}
      </ul>

      {modelVersion && (
        <div className="pt-2 border-t border-border flex items-center justify-between text-[11px] text-slate-400 font-mono">
          <span>Model Architecture:</span>
          <span className="text-slate-300">{modelVersion}</span>
        </div>
      )}
    </div>
  );
}
