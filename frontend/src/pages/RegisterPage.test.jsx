import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import RegisterPage from './RegisterPage';
import { authService } from '../services/authService';

describe('RegisterPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
  });

  it('renders registration form and password requirements checklist', () => {
    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>
    );

    expect(screen.getByLabelText(/^email address$/i, { selector: 'input' })).toBeInTheDocument();
    expect(screen.getByLabelText(/^password$/i, { selector: 'input' })).toBeInTheDocument();
    expect(screen.getByLabelText(/^confirm password$/i, { selector: 'input' })).toBeInTheDocument();
    expect(screen.getByText(/password requirements/i)).toBeInTheDocument();
    expect(screen.getByText(/at least 8 characters/i)).toBeInTheDocument();
  });

  it('displays validation errors when passwords do not match or fields are empty', async () => {
    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>
    );

    const submitBtn = screen.getByRole('button', { name: /^create account$/i });
    fireEvent.click(submitBtn);

    expect(await screen.findByText(/email address is required/i)).toBeInTheDocument();

    // Fill mismatched passwords
    fireEvent.change(screen.getByLabelText(/^email address$/i, { selector: 'input' }), {
      target: { value: 'user@forensics.org' },
    });
    fireEvent.change(screen.getByLabelText(/^password$/i, { selector: 'input' }), {
      target: { value: 'SecurePass123!' },
    });
    fireEvent.change(screen.getByLabelText(/^confirm password$/i, { selector: 'input' }), {
      target: { value: 'DifferentPass123!' },
    });

    fireEvent.click(submitBtn);

    expect(await screen.findByText(/passwords do not match/i)).toBeInTheDocument();
  });

  it('submits form successfully when inputs are valid', async () => {
    const registerSpy = vi.spyOn(authService, 'register').mockResolvedValue({
      email: 'user@forensics.org',
      name: 'user',
      token: 'demo-token-reg-123',
    });

    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText(/^email address$/i, { selector: 'input' }), {
      target: { value: 'user@forensics.org' },
    });
    fireEvent.change(screen.getByLabelText(/^password$/i, { selector: 'input' }), {
      target: { value: 'SecurePass123!' },
    });
    fireEvent.change(screen.getByLabelText(/^confirm password$/i, { selector: 'input' }), {
      target: { value: 'SecurePass123!' },
    });

    fireEvent.click(screen.getByRole('button', { name: /^create account$/i }));

    await waitFor(() => {
      expect(registerSpy).toHaveBeenCalledWith('user@forensics.org', 'SecurePass123!');
    });
  });

  it('displays error banner if authService registration fails', async () => {
    vi.spyOn(authService, 'register').mockRejectedValue(new Error('Email already registered in prototype'));

    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText(/^email address$/i, { selector: 'input' }), {
      target: { value: 'existing@forensics.org' },
    });
    fireEvent.change(screen.getByLabelText(/^password$/i, { selector: 'input' }), {
      target: { value: 'Password123' },
    });
    fireEvent.change(screen.getByLabelText(/^confirm password$/i, { selector: 'input' }), {
      target: { value: 'Password123' },
    });

    fireEvent.click(screen.getByRole('button', { name: /^create account$/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent(/email already registered in prototype/i);
  });
});
