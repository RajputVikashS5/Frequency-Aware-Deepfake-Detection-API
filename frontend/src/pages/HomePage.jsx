import React from 'react';
import { Link } from 'react-router-dom';
import PageLayout from '../components/layout/PageLayout';
import {
  ArrowRight,
  Shield,
  Layers,
  Cpu,
  Activity,
  FileCheck2,
  Lock,
  Sliders,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';

export default function HomePage() {
  return (
    <PageLayout>
      <div className="space-y-16">
        {/* Hero Section */}
        <section className="relative overflow-hidden rounded-2xl bg-card border border-border p-8 sm:p-12 shadow-xl">
          <div className="max-w-3xl space-y-6">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-mono font-medium bg-card-subtle text-accent-cyan border border-border-bright">
              <span className="w-1.5 h-1.5 rounded-full bg-accent-cyan" />
              <span>B.Tech CSE-AIML Academic Project</span>
            </div>

            <h1 className="text-3xl sm:text-5xl font-extrabold text-slate-100 tracking-tight leading-tight">
              Frequency-Aware Deepfake Detection &amp; Image Forensics
            </h1>

            <p className="text-sm sm:text-base text-slate-300 leading-relaxed max-w-2xl">
              An AI-assisted forensic platform combining spatial RGB cues with 2D Fast Fourier Transform (FFT) and Haar discrete wavelet (DWT) representations to detect generative manipulation in facial photography.
            </p>

            <div className="flex flex-wrap gap-4 pt-2">
              <Link
                to="/analyze"
                className="inline-flex items-center space-x-2 px-6 py-3 rounded-lg text-sm font-semibold text-canvas bg-accent-cyan hover:bg-accent-cyan-light shadow-lg transition-colors"
              >
                <span>Analyze Image</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/about"
                className="inline-flex items-center space-x-2 px-5 py-3 rounded-lg text-sm font-medium text-slate-200 bg-card-subtle hover:bg-card-hover border border-border transition-colors"
              >
                <span>Explore Methodology</span>
              </Link>
            </div>
          </div>
        </section>

        {/* Multi-Branch Architecture Overview */}
        <section className="space-y-6">
          <div className="border-b border-border pb-3">
            <h2 className="text-xl font-bold text-slate-100 tracking-tight">
              Dual-Stream Spatial &amp; Frequency Architecture
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Why combining spatial features with frequency spectrums exposes synthesis cues.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Branch 1 */}
            <div className="bg-card p-6 rounded-xl border border-border space-y-3">
              <div className="w-10 h-10 rounded-lg bg-card-subtle border border-border flex items-center justify-center text-accent-blue">
                <Layers className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-slate-100 text-sm">1. Spatial RGB Branch</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Applies convolutional representations to extract pixel-level facial features, texture inconsistencies, and localized Error Level Analysis (ELA) compression boundaries along blending contours.
              </p>
            </div>

            {/* Branch 2 */}
            <div className="bg-card p-6 rounded-xl border border-border space-y-3">
              <div className="w-10 h-10 rounded-lg bg-card-subtle border border-border flex items-center justify-center text-accent-cyan">
                <Activity className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-slate-100 text-sm">2. 2D Fourier (FFT) Branch</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Computes centered log-magnitude 2D Fourier spectra. Transposed convolutions and generative upsamplers frequently inject high-frequency periodic grid harmonics and radial deviations.
              </p>
            </div>

            {/* Branch 3 */}
            <div className="bg-card p-6 rounded-xl border border-border space-y-3">
              <div className="w-10 h-10 rounded-lg bg-card-subtle border border-border flex items-center justify-center text-accent-violet">
                <Sliders className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-slate-100 text-sm">3. Multimodal Fusion</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Fuses spatial embeddings with frequency features in a bottleneck representation, cross-validating edge discrepancies with spectral energy distributions for the final classification.
              </p>
            </div>
          </div>
        </section>

        {/* Workflow Diagram Section */}
        <section className="bg-card rounded-xl border border-border p-8 space-y-6">
          <div className="space-y-1">
            <h2 className="text-lg font-bold text-slate-100">
              System Workflow Pipeline
            </h2>
            <p className="text-xs text-slate-400">
              Sequential data flow from client-side intake to multimodal forensic reporting.
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-6 gap-3 text-center">
            {[
              { step: '01', title: 'Image Upload', desc: 'JPEG, PNG, WebP validation' },
              { step: '02', title: 'Validation', desc: '10 MB & decoding checks' },
              { step: '03', title: 'RGB Branch', desc: 'Face crop & spatial analysis' },
              { step: '04', title: 'FFT Branch', desc: '2D Fourier log magnitude' },
              { step: '05', title: 'Feature Fusion', desc: 'Cross-domain attention' },
              { step: '06', title: 'Forensic Report', desc: 'Classification & findings' },
            ].map((item, idx) => (
              <div key={idx} className="bg-card-subtle border border-border p-3.5 rounded-lg space-y-1.5">
                <span className="font-mono text-[10px] text-accent-cyan font-bold block">{item.step}</span>
                <span className="text-xs font-semibold text-slate-200 block">{item.title}</span>
                <span className="text-[10px] text-slate-500 leading-tight block">{item.desc}</span>
              </div>
            ))}
          </div>
        </section>

        {/* Research Limitations & Responsible Use Note */}
        <section className="bg-card-subtle rounded-xl border border-border p-6 space-y-2">
          <div className="flex items-center space-x-2 text-xs font-semibold text-slate-300">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <span>Research Scope and Responsible Use Statement</span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            This platform is an academic research prototype developed for educational and experimental evaluation. Deepfake detection is an evolving adversarial domain. Frequency-domain artifacts vary based on compression quality, resizing, and optical lens profiles. Predictions should be interpreted as probabilistic evidence rather than definitive forensic certification.
          </p>
        </section>
      </div>
    </PageLayout>
  );
}
