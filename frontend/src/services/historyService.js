import { appConfig } from '../config/appConfig';

/**
 * Service to manage local browser analysis history in localStorage.
 * Does not store large raw files to avoid exceeding storage quotas.
 */

const STORAGE_KEY = appConfig.storageKeys.history;

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

    try {
      const current = this.getHistory();
      // Filter out duplicate if ID already exists
      const filtered = current.filter((item) => item.id !== analysisResult.id);

      // Sanitize record to prevent localStorage quota exhaustion
      const record = {
        id: analysisResult.id,
        timestamp: analysisResult.timestamp || new Date().toISOString(),
        filename: analysisResult.metadata?.filename || 'Untitled Image',
        fileSize: analysisResult.metadata?.fileSize || 0,
        verdict: analysisResult.verdict,
        isManipulated: analysisResult.isManipulated,
        confidencePct: analysisResult.confidencePct,
        scores: analysisResult.scores,
        isDemo: Boolean(analysisResult.isDemo),
        isDiagnostic: Boolean(analysisResult.isDiagnostic),
        // Keep visualization thumbnails only if under safe size limit
        fftSpectrumUrl: analysisResult.visualizations?.fftSpectrumUrl || '',
        originalPreviewUrl:
          typeof analysisResult.visualizations?.originalPreviewUrl === 'string' &&
          analysisResult.visualizations.originalPreviewUrl.length < 300000
            ? analysisResult.visualizations.originalPreviewUrl
            : '',
      };

      const updated = [record, ...filtered].slice(0, 50); // Keep max 50 records
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
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
    const items = this.getHistory();
    return items.find((item) => item.id === id) || null;
  },

  /**
   * Removes a single analysis item by ID.
   * @param {string} id 
   */
  deleteAnalysis(id) {
    if (!id) return;
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
      // 1. Text search
      const matchesQuery = !q || (item.filename && item.filename.toLowerCase().includes(q));

      // 2. Verdict filter
      let matchesFilter = true;
      if (filter === 'real') {
        matchesFilter = !item.isManipulated;
      } else if (filter === 'manipulated') {
        matchesFilter = item.isManipulated;
      }

      return matchesQuery && matchesFilter;
    });
  },
};
