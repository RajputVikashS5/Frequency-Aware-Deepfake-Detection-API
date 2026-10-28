import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, CheckCircle2, Mail, Lock, Eye, EyeOff, Loader2, Check, X } from 'lucide-react';
import PageLayout from '../components/layout/PageLayout';
import { authService } from '../services/authService';

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function RegisterPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [errors, setErrors] = useState({});
  const [errorBanner, setErrorBanner] = useState('');
  const [loading, setLoading] = useState(false);

  // Password strength checks
  const passwordCriteria = [
    { label: 'At least 8 characters', met: form.password.length >= 8 },
    { label: 'Contains a number (0-9)', met: /\d/.test(form.password) },
    { label: 'Contains uppercase letter or symbol', met: /[A-Z!@#$%^&*(),.?":{}|<>]/.test(form.password) },
  ];

  const validate = () => {
    const newErrors = {};

    if (!form.email.trim()) {
      newErrors.email = 'Email address is required.';
    } else if (!EMAIL_REGEX.test(form.email.trim())) {
      newErrors.email = 'Please enter a valid email address.';
    }

    if (!form.password) {
      newErrors.password = 'Password is required.';
    } else if (form.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters.';
    }

    if (!form.confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password.';
    } else if (form.password !== form.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match.';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
    if (errorBanner) {
      setErrorBanner('');
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setErrorBanner('');

    if (!validate()) {
      return;
    }

    setLoading(true);

    try {
      await authService.register(form.email.trim(), form.password);
      navigate('/analyze');
    } catch (registerError) {
      setErrorBanner(registerError.message || 'Registration failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageLayout maxWidth="max-w-md">
      <div className="rounded-2xl border border-border bg-card p-6 sm:p-8 shadow-xl">
        <div className="mb-6 flex items-center justify-between gap-3">
          <div>
            <p className="text-[10px] font-mono uppercase tracking-[0.2em] text-slate-400">Prototype Access</p>
            <h1 className="mt-1 text-2xl font-bold text-slate-100">Create Account</h1>
          </div>
          <Link
            to="/"
            className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-100 transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent-cyan rounded px-1.5 py-0.5"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Home
          </Link>
        </div>

        <div className="mb-6 rounded-xl border border-border bg-card-subtle p-3.5 text-xs text-slate-300">
          <div className="flex items-center gap-2 text-accent-cyan">
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            <span className="font-semibold uppercase tracking-wide text-[11px]">Local Demonstration Mode</span>
          </div>
          <p className="mt-1 leading-relaxed text-slate-400 text-[11px]">
            Registration simulates session access for forensic prototype evaluation. No real external account is stored.
          </p>
        </div>

        {errorBanner && (
          <div
            role="alert"
            className="mb-5 rounded-lg border border-red-800/60 bg-red-950/30 px-3.5 py-2.5 text-xs text-red-300"
          >
            {errorBanner}
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate className="space-y-4">
          <div className="space-y-1">
            <label htmlFor="reg-email" className="block text-xs font-medium text-slate-300">
              Email Address
            </label>
            <div className="relative flex items-center rounded-lg border border-border bg-canvas focus-within:border-accent-cyan focus-within:ring-1 focus-within:ring-accent-cyan transition-colors">
              <Mail className="absolute left-3 h-4 w-4 text-slate-500 pointer-events-none" />
              <input
                id="reg-email"
                type="email"
                name="email"
                value={form.email}
                onChange={handleChange}
                className="w-full bg-transparent pl-9 pr-3 py-2.5 text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none"
                placeholder="researcher@university.edu"
                autoComplete="email"
                required
              />
            </div>
            {errors.email && (
              <p className="text-[11px] text-red-400 mt-1">{errors.email}</p>
            )}
          </div>

          <div className="space-y-1">
            <label htmlFor="reg-password" className="block text-xs font-medium text-slate-300">
              Password
            </label>
            <div className="relative flex items-center rounded-lg border border-border bg-canvas focus-within:border-accent-cyan focus-within:ring-1 focus-within:ring-accent-cyan transition-colors">
              <Lock className="absolute left-3 h-4 w-4 text-slate-500 pointer-events-none" />
              <input
                id="reg-password"
                type={showPassword ? 'text' : 'password'}
                name="password"
                value={form.password}
                onChange={handleChange}
                className="w-full bg-transparent pl-9 pr-10 py-2.5 text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none"
                placeholder="Create password"
                autoComplete="new-password"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-2.5 p-1 text-slate-400 hover:text-slate-200 transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent-cyan rounded"
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            {errors.password && (
              <p className="text-[11px] text-red-400 mt-1">{errors.password}</p>
            )}
          </div>

          {/* Password strength checklist */}
          <div className="p-2.5 rounded-lg bg-card-subtle border border-border/60 space-y-1.5 text-[11px]">
            <span className="text-[10px] font-mono uppercase text-slate-400 block font-semibold">
              Password Requirements
            </span>
            <div className="space-y-1">
              {passwordCriteria.map((c, idx) => (
                <div key={idx} className="flex items-center space-x-1.5">
                  {c.met ? (
                    <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  ) : (
                    <span className="w-1.5 h-1.5 rounded-full bg-slate-600 ml-1 mr-1 shrink-0" />
                  )}
                  <span className={c.met ? 'text-emerald-300' : 'text-slate-500'}>
                    {c.label}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-1">
            <label htmlFor="reg-confirmPassword" className="block text-xs font-medium text-slate-300">
              Confirm Password
            </label>
            <div className="relative flex items-center rounded-lg border border-border bg-canvas focus-within:border-accent-cyan focus-within:ring-1 focus-within:ring-accent-cyan transition-colors">
              <Lock className="absolute left-3 h-4 w-4 text-slate-500 pointer-events-none" />
              <input
                id="reg-confirmPassword"
                type={showConfirmPassword ? 'text' : 'password'}
                name="confirmPassword"
                value={form.confirmPassword}
                onChange={handleChange}
                className="w-full bg-transparent pl-9 pr-10 py-2.5 text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none"
                placeholder="Confirm password"
                autoComplete="new-password"
                required
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute right-2.5 p-1 text-slate-400 hover:text-slate-200 transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent-cyan rounded"
                aria-label={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
              >
                {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            {errors.confirmPassword && (
              <p className="text-[11px] text-red-400 mt-1">{errors.confirmPassword}</p>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 rounded-lg bg-accent-cyan px-4 py-2.5 text-xs font-semibold text-slate-950 transition hover:bg-accent-cyan-light disabled:cursor-not-allowed disabled:opacity-60 flex items-center justify-center gap-2 shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin text-slate-950" />
                <span>Creating Account...</span>
              </>
            ) : (
              <span>Create Account</span>
            )}
          </button>
        </form>

        <p className="mt-6 text-center text-xs text-slate-400">
          Already registered?{' '}
          <Link
            to="/login"
            className="font-semibold text-accent-cyan hover:text-accent-cyan-light underline decoration-accent-cyan/30 underline-offset-4"
          >
            Sign in
          </Link>
        </p>
      </div>
    </PageLayout>
  );
}
