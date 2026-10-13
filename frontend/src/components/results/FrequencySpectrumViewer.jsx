import React, { useState } from 'react';
import { Eye, Info, Maximize2 } from 'lucide-react';

export default function FrequencySpectrumViewer({ fftUrl, isManipulated }) {
  const [showExplanation, setShowExplanation] = useState(false);

  return (
    <div className="bg-card rounded-xl border border-border p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-accent-cyan" />
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200 font-mono">
            2D Fourier (FFT) Magnitude Spectrum
          </h4>
        </div>
        <button
          type="button"
          onClick={() => setShowExplanation(!showExplanation)}
          className="text-slate-400 hover:text-accent-cyan transition-colors"
          title="Explain Spectrum"
        >
          <Info className="w-4 h-4" />
        </button>
      </div>

      {/* Visual Canvas Container */}
      <div className="relative rounded-lg overflow-hidden border border-border bg-canvas aspect-square flex items-center justify-center group">
        {fftUrl ? (
          <img
            src={fftUrl}
            alt="2D FFT Spectrum"
            className="w-full h-full object-contain"
          />
        ) : (
          <div className="text-xs text-slate-500 font-mono">Spectrum Unavailable</div>
        )}

        {/* Frequency quadrant labels */}
        <span className="absolute top-2 left-2 text-[10px] font-mono text-slate-400 bg-card/80 px-1 rounded">
          (-Nyquist)
        </span>
        <span className="absolute bottom-2 right-2 text-[10px] font-mono text-slate-400 bg-card/80 px-1 rounded">
          (+Nyquist)
        </span>
        <span className="absolute bottom-2 left-2 text-[10px] font-mono text-accent-cyan bg-card/80 px-1 rounded">
          Center: DC (0 Hz)
        </span>
      </div>

      <p className="text-[11px] text-slate-400 leading-relaxed">
        Centered log-magnitude representation. Natural photos exhibit smooth radial power decay. Transposed convolutions inject periodic grid harmonics.
      </p>

      {/* Explanatory Drawer */}
      {showExplanation && (
        <div className="bg-card-subtle p-3 rounded-lg border border-border-bright text-xs text-slate-300 space-y-1.5 animate-fadeIn">
          <span className="font-semibold text-slate-100 block text-[11px]">Interpretation Guide:</span>
          <p className="text-[11px] leading-relaxed text-slate-400">
            • <strong>Center Point:</strong> Zero-frequency DC component containing overall brightness.
          </p>
          <p className="text-[11px] leading-relaxed text-slate-400">
            • <strong>Radial Distance:</strong> Higher frequencies correspond to edges, fine textures, and camera sensor noise.
          </p>
          <p className="text-[11px] leading-relaxed text-slate-400">
            • <strong>Generative Artifacts:</strong> Deepfake upsampling frequently leaves elevated high-frequency cross patterns or satellite dots.
          </p>
        </div>
      )}
    </div>
  );
}
