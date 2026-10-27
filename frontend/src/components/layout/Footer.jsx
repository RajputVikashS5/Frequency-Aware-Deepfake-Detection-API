import React from 'react';
import { Link } from 'react-router-dom';
import { Shield, ExternalLink } from 'lucide-react';
import { appConfig } from '../../config/appConfig';

export default function Footer() {
  return (
    <footer className="bg-card border-t border-border mt-auto no-print">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-10">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8 text-xs">
          {/* Col 1: Overview */}
          <div className="space-y-3 md:col-span-2">
            <div className="flex items-center space-x-2">
              <Shield className="w-4 h-4 text-accent-cyan" />
              <span className="font-bold text-sm text-slate-100">{appConfig.appName}</span>
            </div>
            <p className="text-slate-400 leading-relaxed max-w-md">
              Frequency-Aware Deepfake Detection and Image Forensics Using Spatial-Frequency Fusion. Investigates complementary 2D Fourier (FFT) and discrete wavelet (DWT) signatures alongside spatial RGB features.
            </p>
            <div className="text-[11px] text-slate-400 font-mono">
            
            </div>
          </div>

          {/* Col 2: Navigation */}
          <div className="space-y-2">
            <span className="font-semibold text-slate-200 block text-xs uppercase tracking-wider font-mono">
              System Pages
            </span>
            <ul className="space-y-1.5 text-slate-400">
              <li><Link to="/" className="hover:text-accent-cyan transition-colors">Home & Overview</Link></li>
              <li><Link to="/analyze" className="hover:text-accent-cyan transition-colors">Analyze Image</Link></li>
              <li><Link to="/history" className="hover:text-accent-cyan transition-colors">Inspection History</Link></li>
              <li><Link to="/about" className="hover:text-accent-cyan transition-colors">Methodology & Theory</Link></li>
            </ul>
          </div>

          {/* Col 3: Research Notes */}
          <div className="space-y-2">
            <span className="font-semibold text-slate-200 block text-xs uppercase tracking-wider font-mono">
              Technology Stack
            </span>
            <ul className="space-y-1.5 text-slate-400">
              <li>React + Vite + Tailwind CSS</li>
              <li>Axios API Architecture</li>
              <li>Browser File API Validation</li>
              <li>Recharts & Canvas FFT Spectrum</li>
            </ul>
          </div>
        </div>

        {/* Disclaimer Bar */}
        <div className="border-t border-border pt-6 flex flex-col sm:flex-row items-center justify-between text-[11px] text-slate-400 gap-3">
          <p>
            {appConfig.disclaimers.researchNotice}
          </p>
          <div className="flex items-center space-x-4 shrink-0">
            <span>Client Version {appConfig.appVersion}</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
