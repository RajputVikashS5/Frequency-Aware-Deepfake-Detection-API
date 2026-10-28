import { appConfig } from '../config/appConfig';

/**
 * Frontend-only authentication simulation.
 * Stores simulated user profile and dummy bearer token in sessionStorage.
 * NOTE: For UI evaluation and prototype demonstration only.
 */

const USER_KEY = appConfig.storageKeys.sessionUser;
const TOKEN_KEY = appConfig.storageKeys.authToken || 'imageforensics_demo_token';

export const authService = {
  getCurrentUser() {
    try {
      const data = sessionStorage.getItem(USER_KEY);
      return data ? JSON.parse(data) : null;
    } catch {
      return null;
    }
  },

  getToken() {
    try {
      return sessionStorage.getItem(TOKEN_KEY) || null;
    } catch {
      return null;
    }
  },

  async login(email, password) {
    // Artificial prototype latency
    await new Promise((res) => setTimeout(res, 350));

    if (!email || !password) {
      throw new Error('Please provide both email and password.');
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      throw new Error('Please enter a valid email address.');
    }

    const mockToken = `demo-token-${Date.now().toString(36)}-${Math.random().toString(36).substring(2, 9)}`;
    const mockUser = {
      email,
      name: email.split('@')[0],
      token: mockToken,
      loggedInAt: new Date().toISOString(),
    };

    sessionStorage.setItem(USER_KEY, JSON.stringify(mockUser));
    sessionStorage.setItem(TOKEN_KEY, mockToken);
    return mockUser;
  },

  async register(email, password) {
    await new Promise((res) => setTimeout(res, 350));

    if (!email || !password) {
      throw new Error('Please fill in all required registration fields.');
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      throw new Error('Please enter a valid email address.');
    }

    if (password.length < 8) {
      throw new Error('Password must be at least 8 characters long.');
    }

    const mockToken = `demo-token-${Date.now().toString(36)}-${Math.random().toString(36).substring(2, 9)}`;
    const mockUser = {
      email,
      name: email.split('@')[0],
      token: mockToken,
      registeredAt: new Date().toISOString(),
    };

    sessionStorage.setItem(USER_KEY, JSON.stringify(mockUser));
    sessionStorage.setItem(TOKEN_KEY, mockToken);
    return mockUser;
  },

  logout() {
    sessionStorage.removeItem(USER_KEY);
    sessionStorage.removeItem(TOKEN_KEY);
  },

  isAuthenticated() {
    return Boolean(this.getCurrentUser());
  },
};
