import React, { useMemo, useState } from 'react';
import { Download, Maximize2, Minus, Plus, RotateCcw } from 'lucide-react';

const modes = [
  ['original', 'Original image', 'originalPreviewUrl'],
  ['rgb', 'RGB Grad-CAM', null],
  ['fft', 'FFT spectrum', 'fftSpectrumUrl'],
  ['dwt', 'Haar DWT', 'dwtSubbandsUrl'],
  ['ela', 'ELA / spatial heatmap', 'spatialHeatmapUrl'],
];

export default function ForensicImageViewer({ visualizations }) {
  const [mode, setMode] = useState('original');
  const [zoom, setZoom] = useState(1);
  const [opacity, setOpacity] = useState(0.8);
  const [fullscreen, setFullscreen] = useState(false);
  const selected = useMemo(() => modes.find(([key]) => key === mode) || modes[0], [mode]);
  const imageUrl = selected[2] ? visualizations?.[selected[2]] : null;

  function downloadCurrent() {
    if (!imageUrl) return;
    const link = document.createElement('a');
    link.href = imageUrl;
    link.download = `forensic-${mode}.jpg`;
    link.click();
  }

  return (
    <section className={`rounded-xl border border-border bg-card p-4 space-y-4 ${fullscreen ? 'fixed inset-4 z-50 overflow-auto' : ''}`} aria-labelledby="viewer-heading">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <h3 id="viewer-heading" className="text-sm font-bold uppercase tracking-wider text-slate-200 font-mono">Interactive Forensic Viewer</h3>
        <div className="flex flex-wrap gap-2">
          {modes.map(([key, label]) => (
            <button key={key} type="button" onClick={() => setMode(key)} className={`px-2 py-1 rounded text-[10px] font-mono border ${mode === key ? 'border-accent-cyan text-accent-cyan' : 'border-border text-slate-400'}`}>
              {label}
            </button>
          ))}
        </div>
      </div>
      <div className="relative rounded-lg overflow-hidden border border-border bg-canvas min-h-72 flex items-center justify-center">
        {imageUrl ? (
          <img src={imageUrl} alt={selected[1]} className="max-h-[65vh] max-w-full object-contain transition-transform" style={{ transform: `scale(${zoom})`, opacity: mode === 'original' ? 1 : opacity }} />
        ) : (
          <p className="text-xs text-slate-500 font-mono">Visualization unavailable for this mode.</p>
        )}
      </div>
      <div className="flex flex-wrap items-center gap-3 text-xs font-mono text-slate-400">
        <button type="button" onClick={() => setZoom((value) => Math.min(3, value + 0.25))} title="Zoom in"><Plus className="w-4 h-4" /></button>
        <button type="button" onClick={() => setZoom((value) => Math.max(0.5, value - 0.25))} title="Zoom out"><Minus className="w-4 h-4" /></button>
        <button type="button" onClick={() => setZoom(1)} title="Reset zoom"><RotateCcw className="w-4 h-4" /></button>
        <label className="flex items-center gap-2">Overlay opacity <input type="range" min="0.1" max="1" step="0.05" value={opacity} onChange={(event) => setOpacity(Number(event.target.value))} /></label>
        <button type="button" onClick={() => setFullscreen((value) => !value)} title="Fullscreen"><Maximize2 className="w-4 h-4" /></button>
        <button type="button" onClick={downloadCurrent} title="Download visualization"><Download className="w-4 h-4" /></button>
      </div>
      <p className="text-[11px] text-slate-500 leading-relaxed">
        {mode === 'rgb'
          ? 'Grad-CAM is unavailable because the current inference adapter does not expose a gradient-backed target layer.'
          : 'FFT spectrum is a frequency-domain representation, not a spatial manipulation map. Diagnostic visualizations are forensic indicators and require corroboration.'}
      </p>
    </section>
  );
}
