interface ConfidenceIndicatorProps {
  confidence: number;
  label?: string;
}

export default function ConfidenceIndicator({
  confidence,
  label = 'Model Confidence',
}: ConfidenceIndicatorProps) {
  const pct = Math.round(confidence * 100);
  const clamped = Math.max(0, Math.min(100, pct));

  const color =
    clamped >= 75 ? 'from-emerald-500 to-teal-500' : clamped >= 50 ? 'from-amber-500 to-orange-500' : 'from-red-500 to-rose-500';

  return (
    <div>
      <div className="mb-1.5 flex items-center justify-between">
        <span className="text-xs font-medium text-slate-400">{label}</span>
        <span className="text-sm font-bold text-slate-100">{clamped}%</span>
      </div>
      <div className="h-2.5 w-full overflow-hidden rounded-full bg-white/10">
        <div
          className={`h-full rounded-full bg-gradient-to-r ${color} transition-all duration-700`}
          style={{ width: `${clamped}%` }}
          role="progressbar"
          aria-valuenow={clamped}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`${label}: ${clamped}%`}
        />
      </div>
      <p className="mt-1.5 text-xs text-slate-600">
        Confidence reflects model certainty, not the probability that the claim is objectively true.
      </p>
    </div>
  );
}
