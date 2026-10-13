import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, Lock, Mail, ShieldCheck } from 'lucide-react';
import PageLayout from '../components/layout/PageLayout';
import { authService } from '../services/authService';

export default function LoginPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError('');

    try {
      await authService.login(form.email, form.password);
      navigate('/analyze');
    } catch (loginError) {
      setError(loginError.message || 'Login failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageLayout maxWidth="max-w-2xl">
      <div className="rounded-2xl border border-border bg-card p-6 sm:p-8 shadow-xl">
        <div className="mb-6 flex items-center justify-between gap-3">
          <div>
            <p className="text-[10px] font-mono uppercase tracking-[0.2em] text-slate-400">Prototype Access</p>
            <h1 className="mt-2 text-2xl font-bold text-slate-100">Login</h1>
          </div>
          <Link to="/" className="inline-flex items-center gap-2 text-xs text-slate-400 hover:text-slate-100">
            <ArrowLeft className="h-3.5 w-3.5" />
            Home
          </Link>
        </div>

        <div className="mb-6 rounded-xl border border-border bg-card-subtle p-4 text-xs text-slate-300">
          <div className="flex items-center gap-2 text-accent-cyan">
            <ShieldCheck className="h-4 w-4" />
            <span className="font-semibold uppercase tracking-wide">Demo-only authentication</span>
          </div>
          <p className="mt-2 leading-relaxed text-slate-400">
            This is a local frontend simulation only. No server-side authentication, password hashing, or secure session is used in this prototype.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <label className="block space-y-2 text-sm text-slate-300">
            <span>Email</span>
            <div className="flex items-center gap-3 rounded-lg border border-border bg-canvas px-3 py-2.5">
              <Mail className="h-4 w-4 text-slate-500" />
              <input
                type="email"
                name="email"
                value={form.email}
                onChange={handleChange}
                className="w-full bg-transparent text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none"
                placeholder="name@example.com"
                autoComplete="email"
                required
              />
            </div>
          </label>

          <label className="block space-y-2 text-sm text-slate-300">
            <span>Password</span>
            <div className="flex items-center gap-3 rounded-lg border border-border bg-canvas px-3 py-2.5">
              <Lock className="h-4 w-4 text-slate-500" />
              <input
                type="password"
                name="password"
                value={form.password}
                onChange={handleChange}
                className="w-full bg-transparent text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none"
                placeholder="Enter demo password"
                autoComplete="current-password"
                required
              />
            </div>
          </label>

          {error && (
            <div className="rounded-lg border border-red-800/60 bg-red-950/20 px-3 py-2 text-xs text-red-300">{error}</div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-accent-cyan px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-accent-cyan-light disabled:cursor-not-allowed disabled:opacity-70"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <p className="mt-6 text-center text-xs text-slate-400">
          Need an account?{' '}
          <Link to="/register" className="font-semibold text-accent-cyan hover:text-accent-cyan-light">
            Create one
          </Link>
        </p>
      </div>
    </PageLayout>
  );
}
