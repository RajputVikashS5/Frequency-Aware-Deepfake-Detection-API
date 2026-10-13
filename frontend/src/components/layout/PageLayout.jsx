import React from 'react';
import Navbar from './Navbar';
import Footer from './Footer';
import { appConfig } from '../../config/appConfig';
import { AlertCircle } from 'lucide-react';

export default function PageLayout({ children, maxWidth = 'max-w-7xl' }) {
  return (
    <div className="min-h-screen bg-canvas text-slate-100 flex flex-col font-sans selection:bg-accent-cyan/20 selection:text-accent-cyan">
      <Navbar />

      {/* Demo Mode Notice Banner */}
      {appConfig.isDemoMode && (
        <div className="bg-card-subtle border-b border-border text-xs text-slate-300 py-1.5 px-4 text-center no-print">
          <div className="max-w-7xl mx-auto flex items-center justify-center space-x-2">
            <span className="w-1.5 h-1.5 rounded-full bg-accent-violet animate-pulse" />
            <span className="font-semibold text-accent-violet">Demo Mode Active:</span>
            <span>Running client-side demonstration data. Backend AI models will be integrated in future phases.</span>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <main className={`flex-1 w-full ${maxWidth} mx-auto px-4 sm:px-6 py-8`}>
        {children}
      </main>

      <Footer />
    </div>
  );
}
