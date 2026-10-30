import React from 'react';
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

export default function FFTSpectrum({ imageUrl, profile = [], energy = {} }) {
  return (
    <section className="rounded-xl border border-border bg-card p-5 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200 font-mono">FFT Magnitude Spectrum</h3>
        <span className="text-[10px] text-slate-500 font-mono">DC center / Nyquist edge</span>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="aspect-square rounded-lg bg-canvas border border-border flex items-center justify-center">
          {imageUrl ? <img src={imageUrl} alt="Measured FFT magnitude spectrum" className="w-full h-full object-contain" /> : <span className="text-xs text-slate-500">FFT unavailable</span>}
        </div>
        <div className="h-64 self-center">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={profile}><XAxis dataKey="frequency" tick={{ fontSize: 9 }} stroke="#64748b" /><YAxis tick={{ fontSize: 9 }} stroke="#64748b" /><Tooltip /><Area dataKey="energy" stroke="#a78bfa" fill="#7c3aed" fillOpacity={0.25} /></AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="grid grid-cols-3 gap-3 text-[10px] font-mono text-slate-400">
        <span>Low: {energy.low ?? 'N/A'}</span><span>Mid: {energy.mid ?? 'N/A'}</span><span>High: {energy.high ?? 'N/A'}</span>
      </div>
    </section>
  );
}
