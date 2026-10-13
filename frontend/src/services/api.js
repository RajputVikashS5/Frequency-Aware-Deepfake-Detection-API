import axios from 'axios';
import { appConfig } from '../config/appConfig';

/**
 * Pre-configured Axios instance for future FastAPI backend calls.
 */
export const apiClient = axios.create({
  baseURL: appConfig.apiBaseUrl,
  timeout: 45000,
  headers: {
    'Accept': 'application/json',
  },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    let message = 'An unexpected network error occurred.';
    if (error.response) {
      message = error.response.data?.detail || `Server returned error ${error.response.status}`;
    } else if (error.request) {
      message = `Cannot reach backend at ${appConfig.apiBaseUrl}. Please ensure the server is running.`;
    } else {
      message = error.message;
    }
    return Promise.reject(new Error(message));
  }
);
