import React from 'react';
import PageLayout from '../components/layout/PageLayout';
import {
  Shield,
  Layers,
  Activity,
  Sliders,
  AlertTriangle,
  Cpu,
  CheckCircle2,
  FileCheck2,
  ArrowRight,
} from 'lucide-react';

export default function Methodology() {
  return (
    <PageLayout maxWidth="max-w-5xl">
      <div className="space-y-12">
        {/* Title Header */}
        <div className="border-b border-border pb-6">
          <div className="flex items-center space-x-2 text-xs font-mono text-accent-cyan uppercase tracking-wider mb-2">
            <Shield className="w-4 h-4" />
            <span>Forensic Architecture &amp; Theory</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-100 tracking-tight">
            Methodology &amp; System Architecture
          </h1>
          <p className="text-sm text-slate-400 mt-2 max-w-3xl leading-relaxed">
            Technical foundations of frequency-aware deepfake detection combining spatial RGB features, 2D Fast Fourier Transform (FFT) log-magnitude spectra, and Haar discrete wavelet (DWT) decomposition.
          </p>
        </div>

        {/* 1. Problem and Scientific Motivation */}
        <section className="bg-card rounded-2xl border border-border p-6 sm:p-8 space-y-4 shadow-xl">
          <div className="flex items-center space-x-3">
            <span className="w-8 h-8 rounded-lg bg-card-subtle border border-border flex items-center justify-center text-accent-cyan font-mono font-bold text-xs">
              01
            </span>
            <h2 className="text-lg font-bold text-slate-100">
              The Forensic Challenge &amp; Motivation
            </h2>
          </div>
          <p className="text-xs sm:text-sm leading-relaxed text-slate-300">
            Modern generative models—such as Generative Adversarial Networks (StyleGAN, StarGAN), diffusion models (Stable Diffusion, Midjourney), and latent autoencoders—achieve remarkable photorealism in the spatial domain. Traditional spatial detectors trained purely on pixel RGB statistics frequently struggle when facing post-processing compression or novel generative generators.
          </p>
          <p className="text-xs sm:text-sm leading-relaxed text-slate-400">
            However, digital image synthesis relies heavily on upsampling operators, transposed convolutions, and patch-level blending. These structural operations leave persistent, characteristic anomalies in the frequency domain—manifesting as periodic spectral peaks, elevated high-frequency tails, and wavelet energy imbalances that human eyes cannot perceive.
          </p>
        </section>

        {/* 2. System Architecture Flowchart (SVG / CSS Diagram) */}
        <section className="bg-card rounded-2xl border border-border p-6 sm:p-8 space-y-6 shadow-xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <span className="w-8 h-8 rounded-lg bg-card-subtle border border-border flex items-center justify-center text-accent-blue font-mono font-bold text-xs">
                02
              </span>
              <h2 className="text-lg font-bold text-slate-100">
                End-to-End System Pipeline
              </h2>
            </div>
            <span className="text-[11px] font-mono text-slate-400">
              Multi-Branch Fusion Pipeline
            </span>
          </div>

          {/* Architecture Visual Diagram */}
          <div className="bg-card-subtle rounded-xl border border-border p-5 overflow-x-auto">
            <div className="min-w-[700px] flex items-center justify-between gap-2 text-center text-xs">
              {/* Step 1: Upload */}
              <div className="flex-1 bg-card border border-border-bright rounded-lg p-3 space-y-1">
                <span className="font-mono text-[10px] text-accent-cyan font-bold block">01. INTAKE</span>
                <span className="font-bold text-slate-200 block text-xs">Image Upload</span>
                <span className="text-[10px] text-slate-400 block font-mono">JPG, PNG, WebP</span>
              </div>

              <ArrowRight className="w-4 h-4 text-slate-500 shrink-0" />

              {/* Step 2: Validation */}
              <div className="flex-1 bg-card border border-border-bright rounded-lg p-3 space-y-1">
                <span className="font-mono text-[10px] text-accent-cyan font-bold block">02. VERIFY</span>
                <span className="font-bold text-slate-200 block text-xs">Validation</span>
                <span className="text-[10px] text-slate-400 block font-mono">10MB &amp; Decode</span>
              </div>

              <ArrowRight className="w-4 h-4 text-slate-500 shrink-0" />

              {/* Step 3: Multi-Branch Feature Extraction */}
              <div className="flex-[1.5] bg-card border border-accent-cyan/40 rounded-lg p-3 space-y-1.5 shadow-inner shadow-accent-cyan/5">
                <span className="font-mono text-[10px] text-accent-cyan font-bold block">03. DUAL-STREAM</span>
                <div className="grid grid-cols-2 gap-1 text-[11px] font-semibold text-slate-200">
                  <div className="bg-card-subtle p-1 rounded border border-border text-accent-blue">RGB Spatial</div>
                  <div className="bg-card-subtle p-1 rounded border border-border text-accent-cyan">FFT Spectral</div>
                </div>
                <span className="text-[10px] text-slate-400 block font-mono">+ Wavelet DWT Subbands</span>
              </div>

              <ArrowRight className="w-4 h-4 text-slate-500 shrink-0" />

              {/* Step 4: Fusion */}
              <div className="flex-1 bg-card border border-border-bright rounded-lg p-3 space-y-1">
                <span className="font-mono text-[10px] text-accent-violet font-bold block">04. BOTTLENECK</span>
                <span className="font-bold text-slate-200 block text-xs">Feature Fusion</span>
                <span className="text-[10px] text-slate-400 block font-mono">Attention Concatenation</span>
              </div>

              <ArrowRight className="w-4 h-4 text-slate-500 shrink-0" />

              {/* Step 5: Classification / Results */}
              <div className="flex-[1.2] bg-card border border-emerald-500/40 rounded-lg p-3 space-y-1">
                <span className="font-mono text-[10px] text-emerald-400 font-bold block">05. OUTPUT</span>
                <span className="font-bold text-slate-200 block text-xs">Forensic Results</span>
                <span className="text-[10px] text-slate-400 block font-mono">Spectrum &amp; Verdict</span>
              </div>
            </div>
          </div>
        </section>

        {/* 3. Deep-Dive: Multi-Branch Feature Streams */}
        <section className="space-y-6">
          <div className="border-b border-border pb-3">
            <h2 className="text-xl font-bold text-slate-100 tracking-tight">
              Feature Representations &amp; Mathematical Principles
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Detailed breakdown of the complementary spatial, Fourier, and wavelet modalities.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Stream 1 */}
            <div className="bg-card p-6 rounded-xl border border-border space-y-3 shadow-md">
              <div className="w-9 h-9 rounded-lg bg-card-subtle border border-border flex items-center justify-center text-accent-blue">
                <Layers className="w-4 h-4" />
              </div>
              <h3 className="font-bold text-slate-100 text-sm">Spatial RGB Stream</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Applies standard convolutional backbones (ResNet18) to analyze localized facial textures, color inconsistencies, and boundary gradient transitions. Error Level Analysis (ELA) exposes differences in JPEG compression ratios between face regions and backgrounds.
              </p>
            </div>

            {/* Stream 2 */}
            <div className="bg-card p-6 rounded-xl border border-border space-y-3 shadow-md">
              <div className="w-9 h-9 rounded-lg bg-card-subtle border border-border flex items-center justify-center text-accent-cyan">
                <Activity className="w-4 h-4" />
              </div>
              <h3 className="font-bold text-slate-100 text-sm">2D Fourier Transform (FFT)</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Computes centered 2D Fast Fourier Transform log-magnitude spectra. Natural photographs adhere to a smooth azimuthal 1/f power law. Transposed convolutions introduce periodic cross-hair harmonics and anomalous radial high-frequency spikes.
              </p>
            </div>

            {/* Stream 3 */}
            <div className="bg-card p-6 rounded-xl border border-border space-y-3 shadow-md">
              <div className="w-9 h-9 rounded-lg bg-card-subtle border border-border flex items-center justify-center text-accent-violet">
                <Sliders className="w-4 h-4" />
              </div>
              <h3 className="font-bold text-slate-100 text-sm">Haar Wavelet (DWT)</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Decomposes the image into four multi-resolution quadrants: LL (approximation), HL (vertical), LH (horizontal), and HH (diagonal). Generative interpolation often leaves high-frequency noise residue specifically isolated in the diagonal subband.
              </p>
            </div>
          </div>
        </section>

        {/* 4. Evaluation Protocol and Metrics */}
        <section className="bg-card rounded-2xl border border-border p-6 sm:p-8 space-y-4 shadow-xl">
          <div className="flex items-center space-x-3">
            <span className="w-8 h-8 rounded-lg bg-card-subtle border border-border flex items-center justify-center text-accent-violet font-mono font-bold text-xs">
              03
            </span>
            <h2 className="text-lg font-bold text-slate-100">
              Evaluation Metrics &amp; Ablation Protocol
            </h2>
          </div>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
            In forensic evaluation, class imbalance between authentic and synthetic imagery can skew naive accuracy measurements. The project architecture relies on:
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
            <div className="bg-card-subtle p-4 rounded-xl border border-border space-y-1">
              <span className="font-bold text-xs text-accent-cyan block">Precision &amp; Recall</span>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Balances false positives against missed generative fakes, crucial in legal and journalistic contexts.
              </p>
            </div>
            <div className="bg-card-subtle p-4 rounded-xl border border-border space-y-1">
              <span className="font-bold text-xs text-accent-blue block">F1-Score</span>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Harmonic mean providing a stable single-value metric under unbalanced dataset conditions.
              </p>
            </div>
            <div className="bg-card-subtle p-4 rounded-xl border border-border space-y-1">
              <span className="font-bold text-xs text-accent-violet block">ROC-AUC</span>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Area Under the Receiver Operating Characteristic curve, measuring threshold-independent discriminative power.
              </p>
            </div>
          </div>
        </section>

        {/* 5. Scientific Limitations and Responsible Use */}
        <section className="bg-card-subtle rounded-2xl border border-border p-6 sm:p-8 space-y-4">
          <div className="flex items-center space-x-2 text-xs font-semibold text-amber-300">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
            <span>Forensic Scope, Limitations, and Responsible Use</span>
          </div>
          <ul className="list-disc list-inside text-xs space-y-2 text-slate-300 pl-1 leading-relaxed">
            <li>
              <strong>Non-conclusive spectral indicators:</strong> FFT frequency anomalies do not constitute legal proof of synthetic manipulation. Aggressive lossy JPEG re-compression, social media filters, and camera sensor post-processing can also shift high-frequency characteristics.
            </li>
            <li>
              <strong>Generalization constraints:</strong> A model calibrated solely on one generative family (e.g., GANs) may experience domain shift when presented with novel diffusion architectures.
            </li>
            <li>
              <strong>Academic prototype designation:</strong> This software is engineered for academic research, education, and forensic hypothesis testing.
            </li>
          </ul>
        </section>
      </div>
    </PageLayout>
  );
}
