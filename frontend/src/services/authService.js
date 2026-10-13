import { appConfig } from '../config/appConfig';

/**
 * Frontend-only authentication simulation.
 * NOTE: This is for UI evaluation and prototyping only. It is not connected
 * to a server and does NOT store passwords or provide cryptographic security.
 */

const USER_KEY = appConfig.storageKeys.sessionUser;

export const authService = {
  getCurrentUser() {
    try {
      const data = sessionStorage.getItem(USER_KEY);
      return data ? JSON.parse(data) : null;
    } catch {
      return null;
    }
  },

  async login(email, password) {
    // Artificial latency
    await new Promise((res) => setTimeout(res, 600));

    if (!email || !password) {
      throw new Error('Please provide both email and password.');
    }

    const mockUser = {
      email,
      name: email.split('@')[0],
      loggedInAt: new Date().toISOString(),
    };
    sessionStorage.setItem(USER_KEY, JSON.stringify(mockUser));
    return mockUser;
  },

  async register(email, password) {
    await new Promise((res) => setTimeout(res, 700));

    if (!email || !password) {
      throw new Error('Please fill in all required registration fields.');
    }

    const mockUser = {
      email,
      name: email.split('@')[0],
      registeredAt: new Date().toISOString(),
    };
    sessionStorage.setItem(USER_KEY, JSON.stringify(mockUser));
    return mockUser;
  },

  logout() {
    sessionStorage.removeItem(USER_KEY);
  },

  isAuthenticated() {
    return Boolean(this.getCurrentUser());
  },
};
