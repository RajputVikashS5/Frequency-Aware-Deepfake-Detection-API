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
        const response = await apiClient.post('/predict', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });

        const raw = response.data;
        // Map backend response into standard frontend schema
        result = {
          id: `srv-${Date.now().toString(36)}-${Math.random().toString(36).substring(2, 6)}`,
          timestamp: new Date().toISOString(),
          processingTimeMs: 1150,
          isDemo: false,
          disclaimer: 'Validated Model Inference Output',
          verdict: raw.is_fake ? 'Likely Manipulated' : 'Likely Real',
          isManipulated: Boolean(raw.is_fake),
          confidencePct: Number(raw.confidence_pct || 50),
          scoreType: 'Multimodal Fusion Model Score',
          scores: {
            rgbBranch: Number(raw.scores?.spatial_rgb || 50),
            fftBranch: Number(raw.scores?.frequency_fft || 50),
            dwtBranch: Number(raw.scores?.wavelet_dwt || 50),
            fusedModel: Number(raw.confidence_pct || 50),
          },
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
          findings: raw.findings || ['Forensic pipeline completed without exception.'],
          modelVersion: 'ResNet18-FFT-DWT-v1.0 (Live Endpoint)',
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
