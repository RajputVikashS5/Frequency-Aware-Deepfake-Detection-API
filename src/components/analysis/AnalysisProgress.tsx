import { Loader2 } from 'lucide-react';
import { useReducedMotion } from '@/hooks/useReducedMotion';

interface AnalysisProgressProps {
  mode: 'text_image' | 'text_only';
  onCancel?: () => void;
}

export default function AnalysisProgress({ mode, onCancel }: AnalysisProgressProps) {
  const reduced = useReducedMotion();

  const stages =
    mode === 'text_image'
      ? ['Preparing input', 'Text analysis', 'Image analysis', 'Generating result']
      : ['Preparing input', 'Text analysis', 'Generating result'];

  return (
    <div className="glass-card flex flex-col items-center px-6 py-10 text-center">
      <div className={`mb-6 ${reduced ? '' : 'pulse-glow'} flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-500/20 to-blue-500/10`}>
        <Loader2 size={28} className={`text-cyan-400 ${reduced ? '' : 'animate-spin'}`} />
      </div>

      <h3 className="mb-2 text-lg font-semibold text-slate-100">Analyzing your news content</h3>
      <p className="mb-6 max-w-md text-sm text-slate-400">
        {reduced
          ? 'Please wait while the system processes your request.'
          : 'Your request is being processed. This may take a few moments.'}
      </p>

      <div className="w-full max-w-md space-y-3">
        {stages.map((stage, i) => (
          <div key={stage} className="flex items-center gap-3">
            <div
              className={`flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full border ${
                reduced
                  ? 'border-cyan-400/30 bg-cyan-500/5'
                  : 'border-cyan-400/40 bg-cyan-500/10 animate-pulse'
              }`}
              style={
                !reduced
                  ? { animationDelay: `${i * 400}ms` }
                  : undefined
              }
            >
              <Loader2 size={12} className={reduced ? '' : 'animate-spin text-cyan-400'} />
            </div>
            <span className="text-sm text-slate-300">{stage}</span>
          </div>
        ))}
      </div>

      <p className="mt-6 max-w-sm text-xs text-slate-600">
        {mode === 'text_image'
          ? 'Running text and image analysis sequentially.'
          : 'Running text analysis only.'}
        {' '}Progress shown is indeterminate until the server responds.
      </p>

      {onCancel && (
        <button type="button" onClick={onCancel} className="btn-ghost mt-4">
          Cancel
        </button>
      )}
    </div>
  );
}
