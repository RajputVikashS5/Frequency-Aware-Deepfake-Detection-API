import React from 'react';
import Navbar from './Navbar';
import Footer from './Footer';
import DemoBanner from './DemoBanner';

export default function PageLayout({
  children,
  maxWidth = 'max-w-7xl',
  isDiagnostic = false,
  bannerMessage = null,
}) {
  return (
    <div className="min-h-screen bg-canvas text-slate-100 flex flex-col font-sans selection:bg-accent-cyan/20 selection:text-accent-cyan">
      <Navbar />

      {/* Global Demo / Diagnostic Banner */}
      <DemoBanner isDiagnostic={isDiagnostic} message={bannerMessage} />

      {/* Main Content Area */}
      <main className={`flex-1 w-full ${maxWidth} mx-auto px-4 sm:px-6 py-8`}>
        {children}
      </main>

      <Footer />
    </div>
  );
}
