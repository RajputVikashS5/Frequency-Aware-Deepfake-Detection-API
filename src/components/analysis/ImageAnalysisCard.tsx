import { ImageIcon, ShieldAlert } from 'lucide-react';
import type { ImageAnalysisResult } from '@/types/analysis';
import ConfidenceIndicator from '@/components/analysis/ConfidenceIndicator';

export default function ImageAnalysisCard({ result }: { result: ImageAnalysisResult }) {
  return (
    <div className="glass-card p-5">
      <div className="mb-4 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-500/10">
          <ImageIcon size={18} className="text-violet-400" />
        </div>
        <div>
          <h3 className="text-base font-semibold text-slate-100">Image Analysis</h3>
          {result.model_label && (
            <p className="text-xs text-slate-500">Model label: {result.model_label}</p>
          )}
        </div>
      </div>

      {typeof result.confidence === 'number' && (
        <div className="mb-4">
          <ConfidenceIndicator confidence={result.confidence} label="Image Model Confidence" />
        </div>
      )}

      {result.explanation && (
        <p className="mb-4 text-sm leading-relaxed text-slate-300">{result.explanation}</p>
      )}

      {result.image_text_consistency && (
        <div className="mb-4 rounded-lg bg-white/5 px-3 py-2.5">
          <p className="text-xs font-medium text-slate-400">Image-Text Consistency</p>
          <p className="mt-1 text-sm text-slate-300">{result.image_text_consistency}</p>
        </div>
      )}

      {result.manipulation_signals && result.manipulation_signals.length > 0 && (
        <div>
          <div className="mb-2 flex items-center gap-2">
            <ShieldAlert size={14} className="text-amber-400" />
            <span className="text-xs font-medium text-slate-400">Manipulation Signals</span>
          </div>
          <ul className="space-y-1.5">
            {result.manipulation_signals.map((signal, i) => (
              <li
                key={i}
                className="flex items-start gap-2 rounded-lg bg-amber-500/5 px-3 py-2 text-xs text-slate-300"
              >
                <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-amber-400" />
                {signal}
              </li>
            ))}
          </ul>
        </div>
      )}

      {!result.explanation && !result.manipulation_signals && !result.image_text_consistency && (
        <p className="text-sm text-slate-500">No detailed image analysis was returned.</p>
      )}
    </div>
  );
}
