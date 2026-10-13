import React from 'react';

export default function Methodology() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-8 text-slate-700">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
          Methodology and System Architecture
        </h1>
        <p className="text-sm text-slate-600 mt-1 leading-relaxed">
          Technical foundations of frequency-aware deepfake detection combining spatial, Fourier, and wavelet evidence.
        </p>
      </div>

      {/* Problem & Motivation */}
      <section className="bg-white border border-slate-200 rounded-lg p-6 space-y-3 shadow-sm">
        <h2 className="text-base font-bold text-slate-900">1. Problem and Motivation</h2>
        <p className="text-sm leading-relaxed text-slate-600">
          Deepfake generation techniques (such as GANs, autoencoder-based face swaps, and diffusion models) often produce convincing visual results in the spatial domain. However, many generative architectures leave subtle statistical anomalies in the frequency domain due to upsampling operations, transposed convolutions, and patch-based blending.
        </p>
        <p className="text-sm leading-relaxed text-slate-600">
          This system investigates whether frequency-domain representations—specifically 2D Fourier log-magnitude spectra and discrete wavelet transforms—provide complementary forensic cues to traditional RGB spatial features.
        </p>
      </section>

      {/* Feature Streams */}
      <section className="bg-white border border-slate-200 rounded-lg p-6 space-y-4 shadow-sm">
        <h2 className="text-base font-bold text-slate-900">2. Multi-Modal Feature Family</h2>

        <div className="space-y-3 text-sm">
          <div className="border-l-2 border-slate-300 pl-3">
            <h3 className="font-semibold text-slate-900">Spatial RGB Stream</h3>
            <p className="text-slate-600 text-xs mt-0.5 leading-relaxed">
              Feeds aligned facial crops into an RGB convolutional backbone (ResNet18) and computes Error Level Analysis (ELA) to detect localized compression discontinuities and blending boundaries.
            </p>
          </div>

          <div className="border-l-2 border-slate-300 pl-3">
            <h3 className="font-semibold text-slate-900">2D Fourier Transform (FFT)</h3>
            <p className="text-slate-600 text-xs mt-0.5 leading-relaxed">
              Computes the centered 2D Fast Fourier Transform and its log magnitude. Natural camera captures exhibit a smooth, decaying power-law spectrum. Generative upsamplers often introduce periodic spikes and elevated high-frequency energy.
            </p>
          </div>

          <div className="border-l-2 border-slate-300 pl-3">
            <h3 className="font-semibold text-slate-900">Discrete Wavelet Transform (DWT)</h3>
            <p className="text-slate-600 text-xs mt-0.5 leading-relaxed">
              Decomposes the image into four multi-resolution subbands using Haar wavelets: LL (Approximation), HL (Vertical), LH (Horizontal), and HH (Diagonal). High-frequency residuals in the HH subband expose high-frequency noise discrepancies.
            </p>
          </div>
        </div>
      </section>

      {/* Limitations from README */}
      <section className="bg-white border border-slate-200 rounded-lg p-6 space-y-3 shadow-sm">
        <h2 className="text-base font-bold text-slate-900">3. Scientific Scope and Limitations</h2>
        <p className="text-sm leading-relaxed text-slate-600">
          This project is explicitly research-oriented and does not assume that:
        </p>
        <ul className="list-disc list-inside text-xs space-y-1.5 text-slate-600 pl-2 leading-relaxed">
          <li>Frequency artifacts are always present or unique to deepfakes.</li>
          <li>A single manipulation signal is sufficient across all generative models.</li>
          <li>A confidence score is absolute proof of deception.</li>
          <li>Heavy JPEG compression, resizing, or social media re-encoding will not alter high-frequency profiles.</li>
        </ul>
        <p className="text-xs text-slate-500 pt-2 border-t border-slate-100">
          Every proposed feature family must be validated with appropriate ablation experiments and held-out evaluations.
        </p>
      </section>
    </div>
  );
}
