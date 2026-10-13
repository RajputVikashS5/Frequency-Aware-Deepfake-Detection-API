import React, { useState, useEffect } from 'react';
import { Loader2, Radio, CheckCircle2 } from 'lucide-react';

const STAGES = [
  'Validating file structure & decoding dimensions...',
  'Extracting facial core & boundary gradients...',
  'Computing 2D Fast Fourier Transform (FFT)...',
  'Executing 4-subband Haar Wavelet (DWT) decomposition...',
  'Evaluating spatial-frequency fusion bottleneck...',
];

export default function AnalysisProgress() {
  const [currentStage, setCurrentStage] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentStage((prev) => (prev < STAGES.length - 1 ? prev + 1 : prev));
    }, 320);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="bg-card rounded-xl border border-border p-8 text-center space-y-4">
      <div className="inline-flex p-3 rounded-xl bg-card-subtle text-accent-cyan border border-border-bright">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>

      <div className="space-y-1">
        <h3 className="font-bold text-slate-100 text-sm">
          Executing Spatial-Frequency Forensic Pipeline
        </h3>
        <p className="text-xs font-mono text-accent-cyan">
          {STAGES[currentStage]}
        </p>
      </div>

      <div className="max-w-xs mx-auto flex items-center justify-between pt-2">
        {STAGES.map((_, idx) => (
          <div
            key={idx}
            className={`h-1 flex-1 mx-0.5 rounded-full transition-all duration-300 ${
              idx <= currentStage ? 'bg-accent-cyan' : 'bg-canvas'
            }`}
          />
        ))}
      </div>
    </div>
  );
}
