import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import LoginPage from './LoginPage';
import { authService } from '../services/authService';

describe('LoginPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
  });

  it('renders login form with email, password fields and sign in button', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    expect(screen.getByLabelText(/^email address$/i, { selector: 'input' })).toBeInTheDocument();
    expect(screen.getByLabelText(/^password$/i, { selector: 'input' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^sign in$/i })).toBeInTheDocument();
    expect(screen.getByText(/demo prototype auth/i)).toBeInTheDocument();
  });

  it('toggles password visibility when Eye icon button is clicked', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    const passwordInput = screen.getByLabelText(/^password$/i, { selector: 'input' });
    const toggleBtn = screen.getByRole('button', { name: /^show password$/i });

    expect(passwordInput).toHaveAttribute('type', 'password');
    fireEvent.click(toggleBtn);
    expect(passwordInput).toHaveAttribute('type', 'text');
    expect(screen.getByRole('button', { name: /^hide password$/i })).toBeInTheDocument();
  });

  it('shows client-side validation errors when submitting empty or invalid email', async () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    const submitBtn = screen.getByRole('button', { name: /^sign in$/i });
    fireEvent.click(submitBtn);

    expect(await screen.findByText(/email address is required/i)).toBeInTheDocument();
    expect(screen.getByText(/password is required/i)).toBeInTheDocument();

    // Fill invalid email
    const emailInput = screen.getByLabelText(/^email address$/i, { selector: 'input' });
    fireEvent.change(emailInput, { target: { value: 'not-an-email' } });
    fireEvent.click(submitBtn);

    expect(await screen.findByText(/please enter a valid email address/i)).toBeInTheDocument();
  });

  it('submits form successfully and calls authService.login', async () => {
    const loginSpy = vi.spyOn(authService, 'login').mockResolvedValue({
      email: 'tester@forensics.ai',
      name: 'tester',
      token: 'demo-token-123',
    });

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText(/^email address$/i, { selector: 'input' }), {
      target: { value: 'tester@forensics.ai' },
    });
    fireEvent.change(screen.getByLabelText(/^password$/i, { selector: 'input' }), {
      target: { value: 'ValidPassword123!' },
    });

    fireEvent.click(screen.getByRole('button', { name: /^sign in$/i }));

    await waitFor(() => {
      expect(loginSpy).toHaveBeenCalledWith('tester@forensics.ai', 'ValidPassword123!');
    });
  });

  it('displays error banner if authService throws an error', async () => {
    vi.spyOn(authService, 'login').mockRejectedValue(new Error('Invalid demo credentials'));

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText(/^email address$/i, { selector: 'input' }), {
      target: { value: 'test@forensics.ai' },
    });
    fireEvent.change(screen.getByLabelText(/^password$/i, { selector: 'input' }), {
      target: { value: 'password123' },
    });

    fireEvent.click(screen.getByRole('button', { name: /^sign in$/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent(/invalid demo credentials/i);
  });
});
