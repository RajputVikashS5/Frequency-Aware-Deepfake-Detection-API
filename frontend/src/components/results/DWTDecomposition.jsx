import React, { useState } from 'react';

export default function DWTDecomposition({ levels = {}, fallbackUrl }) {
  const [level, setLevel] = useState('level_1');
  const url = levels[level] || fallbackUrl;
  return (
    <section className="rounded-xl border border-border bg-card p-5 space-y-3">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200 font-mono">Haar DWT decomposition</h3>
        <div className="flex gap-2">
          {['level_1', 'level_2'].map((value) => (
            <button key={value} type="button" onClick={() => setLevel(value)} className={`px-2 py-1 text-[10px] font-mono rounded border ${level === value ? 'border-accent-cyan text-accent-cyan' : 'border-border text-slate-400'}`}>
              {value.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>
      <div className="min-h-64 rounded-lg border border-border bg-canvas flex items-center justify-center">
        {url ? <img src={url} alt={`${level} Haar wavelet coefficient grid`} className="max-w-full max-h-[28rem] object-contain" /> : <span className="text-xs text-slate-500">DWT unavailable.</span>}
      </div>
      <p className="text-[11px] text-slate-500">Measured Haar coefficient bands: LL approximation, LH horizontal detail, HL vertical detail, and HH diagonal detail. Values are visualized from the uploaded image.</p>
    </section>
  );
}
