import React, { useState } from 'react';
import { NavLink, Link } from 'react-router-dom';
import { Shield, Menu, X, Radio, LogIn, User } from 'lucide-react';
import { appConfig } from '../../config/appConfig';
import { authService } from '../../services/authService';

export default function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const currentUser = authService.getCurrentUser();

  const links = [
    { to: '/', label: 'Home' },
    { to: '/analyze', label: 'Analyze Image' },
    { to: '/history', label: 'History' },
    { to: '/about', label: 'About & Method' },
  ];

  return (
    <header className="bg-card border-b border-border sticky top-0 z-40 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Brand */}
        <Link to="/" className="flex items-center space-x-3 group">
          <div className="w-9 h-9 rounded-lg bg-card-subtle border border-border-bright flex items-center justify-center text-accent-cyan group-hover:border-accent-cyan transition-colors">
            <Shield className="w-5 h-5" />
          </div>
          <div className="flex flex-col">
            <div className="flex items-center space-x-2">
              <span className="font-bold text-base sm:text-lg text-slate-100 tracking-tight">
                {appConfig.appName}
              </span>
              {appConfig.isDemoMode && (
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-accent-violet/10 text-accent-violet border border-accent-violet/30">
                  DEMO
                </span>
              )}
            </div>
            <span className="text-[10px] text-slate-400 font-mono hidden sm:inline-block">
              Spatial-Frequency Image Forensics
            </span>
          </div>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center space-x-1">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-card-subtle text-accent-cyan border border-border-bright shadow-sm'
                    : 'text-slate-300 hover:text-slate-100 hover:bg-card-hover'
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>

        {/* Right Actions & Auth */}
        <div className="hidden md:flex items-center space-x-3">
          {appConfig.enableAuth && (
            currentUser ? (
              <div className="flex items-center space-x-2 text-xs text-slate-300 bg-card-subtle border border-border px-3 py-1.5 rounded-md">
                <User className="w-3.5 h-3.5 text-accent-cyan" />
                <span className="font-mono">{currentUser.name}</span>
                <button
                  type="button"
                  onClick={() => {
                    authService.logout();
                    window.location.reload();
                  }}
                  className="text-slate-400 hover:text-red-400 ml-2"
                >
                  Logout
                </button>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <Link
                  to="/login"
                  className="px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-slate-100 hover:bg-card-hover rounded-md border border-border transition-colors"
                >
                  Login
                </Link>
                <Link
                  to="/register"
                  className="px-3 py-1.5 text-xs font-semibold text-canvas bg-accent-cyan hover:bg-accent-cyan-light rounded-md transition-colors"
                >
                  Register
                </Link>
              </div>
            )
          )}

          <Link
            to="/analyze"
            className="px-3.5 py-1.5 text-xs font-semibold text-slate-100 bg-accent-blue hover:bg-accent-blue-light rounded-md shadow-sm transition-colors"
          >
            New Analysis
          </Link>
        </div>

        {/* Mobile menu toggle */}
        <div className="md:hidden flex items-center">
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 rounded-md text-slate-400 hover:text-slate-200 hover:bg-card-hover border border-border"
            aria-label="Toggle Navigation Menu"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-border bg-card px-4 pt-3 pb-5 space-y-2">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              onClick={() => setMobileMenuOpen(false)}
              className={({ isActive }) =>
                `block px-3 py-2 rounded-md text-base font-medium ${
                  isActive
                    ? 'bg-card-subtle text-accent-cyan border border-border-bright'
                    : 'text-slate-300 hover:text-slate-100 hover:bg-card-hover'
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
          {appConfig.enableAuth && (
            <div className="pt-3 border-t border-border flex items-center space-x-3">
              <Link
                to="/login"
                onClick={() => setMobileMenuOpen(false)}
                className="w-1/2 text-center py-2 text-xs font-medium text-slate-300 bg-card-subtle border border-border rounded-md"
              >
                Login
              </Link>
              <Link
                to="/register"
                onClick={() => setMobileMenuOpen(false)}
                className="w-1/2 text-center py-2 text-xs font-semibold text-canvas bg-accent-cyan rounded-md"
              >
                Register
              </Link>
            </div>
          )}
        </div>
      )}
    </header>
  );
}
