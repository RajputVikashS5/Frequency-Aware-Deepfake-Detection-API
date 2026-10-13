import React from 'react';
import { Layers } from 'lucide-react';

export default function WaveletViewer({ dwtUrl }) {
  return (
    <div className="bg-card rounded-xl border border-border p-4 space-y-3">
      <div className="flex items-center space-x-2">
        <span className="w-2 h-2 rounded-full bg-accent-violet" />
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200 font-mono">
          Haar Discrete Wavelet (DWT) Subbands
        </h4>
      </div>

      <div className="relative rounded-lg overflow-hidden border border-border bg-canvas aspect-square flex items-center justify-center">
        {dwtUrl ? (
          <img
            src={dwtUrl}
            alt="Haar Wavelet Subbands"
            className="w-full h-full object-contain"
          />
        ) : (
          <div className="text-xs text-slate-500 font-mono">DWT Decomposition Unavailable</div>
        )}
      </div>

      <p className="text-[11px] text-slate-400 leading-relaxed">
        4-Quadrant Haar decomposition: <strong>LL</strong> (Approximation), <strong>HL</strong> (Vertical), <strong>LH</strong> (Horizontal), and <strong>HH</strong> (Diagonal high-pass noise residue).
      </p>
    </div>
  );
}
