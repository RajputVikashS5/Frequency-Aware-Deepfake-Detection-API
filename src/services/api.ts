import { config } from '@/config';
import type { AnalysisResponse, ApiError } from '@/types/analysis';

function buildFormData(payload: {
  headline: string;
  article_text: string;
  source_url?: string;
  mode: string;
  image?: File;
}): FormData {
  const fd = new FormData();
  fd.append('headline', payload.headline);
  fd.append('article_text', payload.article_text);
  fd.append('mode', payload.mode);
  if (payload.source_url) fd.append('source_url', payload.source_url);
  if (payload.image) fd.append('image', payload.image);
  return fd;
}

function mapHttpError(status: number): string {
  switch (status) {
    case 400:
      return 'The request was rejected by the server. Please check your input and try again.';
    case 401:
      return 'Authentication failed. The API may require credentials that are not configured.';
    case 413:
      return 'The uploaded image is too large for the server. Please use a smaller file.';
    case 422:
      return 'The server rejected the input as invalid. Please review your headline and article text.';
    case 429:
      return 'Too many requests. Please wait a moment and try again.';
    case 500:
      return 'The server encountered an internal error. Please try again later.';
    default:
      return `The server returned an error (HTTP ${status}).`;
  }
}

export async function analyzeNews(payload: {
  headline: string;
  article_text: string;
  source_url?: string;
  mode: string;
  image?: File;
}): Promise<AnalysisResponse> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), config.requestTimeoutMs);

  try {
    const url = `${config.apiBaseUrl}${config.endpoints.analyze}`;
    const res = await fetch(url, {
      method: 'POST',
      body: buildFormData(payload),
      signal: controller.signal,
    });

    if (!res.ok) {
      const apiError: ApiError = {
        message: mapHttpError(res.status),
        status: res.status,
      };
      throw apiError;
    }

    let data: unknown;
    try {
      data = await res.json();
    } catch {
      const err: ApiError = {
        message: 'The server returned an invalid response. Please try again.',
        status: res.status,
        code: 'INVALID_JSON',
      };
      throw err;
    }

    if (!data || typeof data !== 'object') {
      const err: ApiError = {
        message: 'The server returned an unexpected response format.',
        code: 'INVALID_RESPONSE',
      };
      throw err;
    }

    return data as AnalysisResponse;
  } catch (e) {
    if (e && typeof e === 'object' && 'message' in e) {
      throw e;
    }
    if (e instanceof DOMException && e.name === 'AbortError') {
      const err: ApiError = {
        message: 'The request timed out. Please try again.',
        code: 'TIMEOUT',
      };
      throw err;
    }
    const err: ApiError = {
      message:
        'Could not connect to the analysis server. Please check your connection and try again.',
      code: 'NETWORK_ERROR',
    };
    throw err;
  } finally {
    clearTimeout(timeout);
  }
}

export async function checkHealth(): Promise<boolean> {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);
    const res = await fetch(`${config.apiBaseUrl}${config.endpoints.health}`, {
      signal: controller.signal,
    });
    clearTimeout(timeout);
    return res.ok;
  } catch {
    return false;
  }
}
