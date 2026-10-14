import { FileText, ListChecks } from 'lucide-react';
import type { TextAnalysisResult } from '@/types/analysis';
import ConfidenceIndicator from '@/components/analysis/ConfidenceIndicator';

export default function TextAnalysisCard({ result }: { result: TextAnalysisResult }) {
  return (
    <div className="glass-card p-5">
      <div className="mb-4 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-500/10">
          <FileText size={18} className="text-cyan-400" />
        </div>
        <div>
          <h3 className="text-base font-semibold text-slate-100">Text Analysis</h3>
          {result.model_label && (
            <p className="text-xs text-slate-500">Model label: {result.model_label}</p>
          )}
        </div>
      </div>

      {typeof result.confidence === 'number' && (
        <div className="mb-4">
          <ConfidenceIndicator confidence={result.confidence} />
        </div>
      )}

      {result.explanation && (
        <p className="mb-4 text-sm leading-relaxed text-slate-300">{result.explanation}</p>
      )}

      {result.indicators && result.indicators.length > 0 && (
        <div>
          <div className="mb-2 flex items-center gap-2">
            <ListChecks size={14} className="text-slate-500" />
            <span className="text-xs font-medium text-slate-400">Detected Indicators</span>
          </div>
          <ul className="space-y-1.5">
            {result.indicators.map((indicator, i) => (
              <li
                key={i}
                className="flex items-start gap-2 rounded-lg bg-white/5 px-3 py-2 text-xs text-slate-300"
              >
                <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-cyan-400" />
                {indicator}
              </li>
            ))}
          </ul>
        </div>
      )}

      {!result.explanation && !result.indicators && (
        <p className="text-sm text-slate-500">No detailed text analysis was returned.</p>
      )}
    </div>
  );
}
