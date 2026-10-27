import { appConfig } from '../config/appConfig';
import { apiClient } from './api';
import { analyzeInDemoMode } from './demoService';
import { historyService } from './historyService';

/**
 * Main analysis facade. Dispatches to Demo Service or Backend API based on appConfig.
 */
export const analysisService = {
  /**
   * Performs image forensic analysis.
   * @param {File} file 
   * @param {string} previewUrl 
   * @returns {Promise<object>}
   */
  async analyzeImage(file, previewUrl) {
    let result;

    if (appConfig.isDemoMode) {
      result = await analyzeInDemoMode(file, previewUrl);
    } else {
      // Future/Live FastAPI backend call
      const formData = new FormData();
      formData.append('file', file);

      try {
        const response = await apiClient.post('/api/v1/analyze', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });

        const raw = response.data;
        // Diagnostics are deliberately not mapped into classification fields.
        result = {
          id: `srv-${Date.now().toString(36)}-${Math.random().toString(36).substring(2, 6)}`,
          timestamp: new Date().toISOString(),
          processingTimeMs: null,
          isDemo: false,
          isDiagnostic: raw.status === 'diagnostic_complete',
          disclaimer: 'DIAGNOSTIC OUTPUT — NOT A VALIDATED MODEL PREDICTION',
          verdict: 'Diagnostic inspection complete',
          isManipulated: null,
          confidencePct: null,
          scoreType: 'No classifier score available',
          scores: null,
          metadata: {
            filename: file.name,
            fileSize: file.size,
            mimeType: file.type,
            sha256Digest: raw.metadata?.sha256 || 'N/A',
          },
          visualizations: {
            originalPreviewUrl: previewUrl,
            faceCropUrl: raw.visualizations?.face_crop,
            fftSpectrumUrl: raw.visualizations?.fft_spectrum,
            dwtSubbandsUrl: raw.visualizations?.dwt_subbands,
            spatialHeatmapUrl: raw.visualizations?.spatial_heatmap,
          },
          spectralProfile: raw.spectral_profile || [],
          findings: raw.findings || [],
          modelVersion: raw.model_version,
          status: raw.status,
          inferenceAvailable: raw.inference_available,
          diagnosticMessage: raw.message,
        };
      } catch (err) {
        console.error('API call failed, unable to complete analysis:', err);
        throw err;
      }
    }

    // Save to local history
    historyService.saveAnalysis(result);
    return result;
  },

  /**
   * Retrieves an analysis by ID from history or memory.
   * @param {string} id 
   * @returns {object | null}
   */
  getAnalysisById(id) {
    return historyService.getAnalysisById(id);
  },
};
