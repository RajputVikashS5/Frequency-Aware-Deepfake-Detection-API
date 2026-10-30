import { appConfig } from '../config/appConfig';

/**
 * Service to manage local browser analysis history in localStorage.
 * Keeps records within storage quotas while preserving diagnostic context.
 */

const STORAGE_KEY = appConfig.storageKeys.history;
const MAX_HISTORY_RECORDS = 50;
const MAX_HISTORY_BYTES = 4 * 1024 * 1024;

// In-memory session cache for full objects in active session
const sessionCache = new Map();

export const historyService = {
  /**
   * Retrieves all stored history records sorted from newest to oldest.
   * @returns {Array<object>}
   */
  getHistory() {
    try {
      const data = localStorage.getItem(STORAGE_KEY);
      if (!data) return [];
      const parsed = JSON.parse(data);
      return Array.isArray(parsed) ? parsed : [];
    } catch (e) {
      console.warn('Failed to read local history from localStorage:', e);
      return [];
    }
  },

  /**
   * Saves an analysis record (sanitizing heavy preview URLs if needed).
   * @param {object} analysisResult 
   */
  saveAnalysis(analysisResult) {
    if (!analysisResult || !analysisResult.id) return;

    // Cache full object in memory for active session
    sessionCache.set(analysisResult.id, analysisResult);

    try {
      const current = this.getHistory();
      const filtered = current.filter((item) => item.id !== analysisResult.id);

      // Safe URL length guard for derived diagnostic visualizations only.
      // Source uploads are deliberately excluded from persistent browser history.
      const safeDataUri = (url) => (typeof url === 'string' && url.length < 200000 ? url : '');

      const record = {
        id: analysisResult.id,
        timestamp: analysisResult.timestamp || new Date().toISOString(),
        filename: analysisResult.metadata?.filename || 'Untitled Image',
        fileSize: analysisResult.metadata?.fileSize || 0,
        verdict: analysisResult.verdict || (analysisResult.isDiagnostic ? 'Diagnostic Complete' : 'Analyzed'),
        isManipulated: analysisResult.isManipulated,
        isInconclusive: Boolean(analysisResult.isInconclusive),
        confidencePct: analysisResult.confidencePct,
        scores: analysisResult.scores || null,
        isDemo: Boolean(analysisResult.isDemo),
        isDiagnostic: Boolean(analysisResult.isDiagnostic),
        disclaimer: analysisResult.disclaimer || '',
        diagnosticMessage: analysisResult.diagnosticMessage || '',
        findings: Array.isArray(analysisResult.findings) ? analysisResult.findings : [],
        modelVersion: analysisResult.modelVersion || '',
        status: analysisResult.status || '',
        scoreType: analysisResult.scoreType || '',
        metadata: analysisResult.metadata || {
          filename: 'Untitled Image',
          fileSize: 0,
        },
        visualizations: {
          originalPreviewUrl: '',
          fftSpectrumUrl: safeDataUri(analysisResult.visualizations?.fftSpectrumUrl),
          dwtSubbandsUrl: safeDataUri(analysisResult.visualizations?.dwtSubbandsUrl),
          faceCropUrl: safeDataUri(analysisResult.visualizations?.faceCropUrl),
          spatialHeatmapUrl: safeDataUri(analysisResult.visualizations?.spatialHeatmapUrl),
        },
        spectralProfile: Array.isArray(analysisResult.spectralProfile) ? analysisResult.spectralProfile : [],
      };

      const updated = [record, ...filtered].slice(0, MAX_HISTORY_RECORDS);
      while (updated.length > 0) {
        const serialized = JSON.stringify(updated);
        if (serialized.length <= MAX_HISTORY_BYTES) {
          localStorage.setItem(STORAGE_KEY, serialized);
          break;
        }
        updated.pop();
      }
    } catch (e) {
      console.warn('Failed to save analysis to localStorage:', e);
    }
  },

  /**
   * Finds an analysis item by its ID.
   * @param {string} id 
   * @returns {object | null}
   */
  getAnalysisById(id) {
    if (!id) return null;
    if (sessionCache.has(id)) {
      return sessionCache.get(id);
    }
    const items = this.getHistory();
    return items.find((item) => item.id === id) || null;
  },

  /**
   * Removes a single analysis item by ID.
   * @param {string} id 
   */
  deleteAnalysis(id) {
    if (!id) return;
    sessionCache.delete(id);
    try {
      const current = this.getHistory();
      const updated = current.filter((item) => item.id !== id);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    } catch (e) {
      console.warn('Failed to delete history item:', e);
    }
  },

  /**
   * Clears the entire local history.
   */
  clearAllHistory() {
    sessionCache.clear();
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (e) {
      console.warn('Failed to clear history:', e);
    }
  },

  /**
   * Searches and filters history items.
   * @param {string} query 
   * @param {'all' | 'real' | 'manipulated'} filter 
   * @returns {Array<object>}
   */
  searchAndFilter(query = '', filter = 'all') {
    const list = this.getHistory();
    const q = query.trim().toLowerCase();

    return list.filter((item) => {
      const matchesQuery = !q || (item.filename && item.filename.toLowerCase().includes(q));

      let matchesFilter = true;
      if (filter === 'real') {
        matchesFilter = item.isManipulated === false;
      } else if (filter === 'manipulated') {
        matchesFilter = item.isManipulated === true;
      }

      return matchesQuery && matchesFilter;
    });
  },
};
