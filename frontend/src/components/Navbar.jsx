import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';

export default function Navbar() {
  const [backendOnline, setBackendOnline] = useState(null);

  useEffect(() => {
    const checkHealth = () => {
      fetch('http://localhost:8000/health')
        .then((res) => res.json())
        .then(() => setBackendOnline(true))
        .catch(() => setBackendOnline(false));
    };

    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const navLinks = [
    { to: '/', label: 'Detector' },
    { to: '/ablation', label: 'Ablation Study' },
    { to: '/methodology', label: 'Methodology' },
  ];

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-40">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Brand / Title */}
        <div className="flex items-center space-x-3">
          <NavLink to="/" className="text-slate-900 font-semibold text-base sm:text-lg hover:text-slate-700 transition-colors">
            Frequency-Aware Deepfake Detection
          </NavLink>
          <span className="hidden sm:inline-block text-xs font-mono font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
            v0.1
          </span>
        </div>

        {/* Navigation & Status */}
        <div className="flex items-center space-x-6">
          <nav className="flex space-x-1">
            {navLinks.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                className={({ isActive }) =>
                  `px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-slate-100 text-slate-900 font-semibold'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`
                }
              >
                {link.label}
              </NavLink>
            ))}
          </nav>

          {/* Backend Status indicator */}
          <div className="hidden md:flex items-center text-xs font-medium text-slate-600 space-x-1.5 border-l border-slate-200 pl-4">
            <span
              className={`w-2 h-2 rounded-full ${
                backendOnline === true
                  ? 'bg-emerald-500'
                  : backendOnline === false
                  ? 'bg-red-500'
                  : 'bg-amber-400'
              }`}
            />
            <span>
              {backendOnline === true
                ? 'Backend: Online'
                : backendOnline === false
                ? 'Backend: Offline'
                : 'Connecting...'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}