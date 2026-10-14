import { Brain, ThumbsUp, ThumbsDown, MinusCircle } from 'lucide-react';
import type { EvidenceItem } from '@/types/analysis';

interface ExplanationPanelProps {
  explanation: string;
  evidence?: EvidenceItem[];
  limitations?: string[];
}

export default function ExplanationPanel({
  explanation,
  evidence = [],
  limitations = [],
}: ExplanationPanelProps) {
  const supporting = evidence.filter((e) => e.classification === 'supports');
  const contradicting = evidence.filter((e) => e.classification === 'contradicts');
  const insufficient = evidence.filter((e) => e.classification === 'insufficient');

  return (
    <div className="glass-card p-5">
      <div className="mb-4 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500/20 to-violet-500/10">
          <Brain size={18} className="text-cyan-400" />
        </div>
        <h3 className="text-base font-semibold text-slate-100">Explainable AI</h3>
      </div>

      <p className="mb-5 text-sm leading-relaxed text-slate-300">{explanation}</p>

      <div className="grid gap-3 sm:grid-cols-3">
        {supporting.length > 0 && (
          <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-3">
            <div className="mb-1.5 flex items-center gap-2">
              <ThumbsUp size={14} className="text-emerald-400" />
              <span className="text-xs font-semibold text-emerald-400">Supporting</span>
            </div>
            <p className="text-xs text-slate-400">
              {supporting.length} source{supporting.length !== 1 ? 's' : ''} support the assessment
            </p>
          </div>
        )}
        {contradicting.length > 0 && (
          <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-3">
            <div className="mb-1.5 flex items-center gap-2">
              <ThumbsDown size={14} className="text-red-400" />
              <span className="text-xs font-semibold text-red-400">Contradicting</span>
            </div>
            <p className="text-xs text-slate-400">
              {contradicting.length} source{contradicting.length !== 1 ? 's' : ''} contradict the assessment
            </p>
          </div>
        )}
        {insufficient.length > 0 && (
          <div className="rounded-xl border border-slate-500/20 bg-slate-500/5 p-3">
            <div className="mb-1.5 flex items-center gap-2">
              <MinusCircle size={14} className="text-slate-400" />
              <span className="text-xs font-semibold text-slate-400">Insufficient</span>
            </div>
            <p className="text-xs text-slate-400">
              {insufficient.length} source{insufficient.length !== 1 ? 's' : ''} with insufficient information
            </p>
          </div>
        )}
      </div>

      {limitations.length > 0 && (
        <div className="mt-4 rounded-xl border border-amber-500/20 bg-amber-500/5 p-3">
          <p className="mb-2 text-xs font-semibold text-amber-400">Limitations</p>
          <ul className="space-y-1">
            {limitations.map((lim, i) => (
              <li key={i} className="text-xs text-slate-400">
                • {lim}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-4 rounded-xl bg-white/5 px-3 py-2.5">
        <p className="text-xs text-slate-500">
          Model predictions and verified facts are shown separately. Predictions are based on
          patterns learned during training; verified facts come from retrieved evidence sources.
        </p>
      </div>
    </div>
  );
}
