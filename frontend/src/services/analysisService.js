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
        const inferenceAvailable = raw.inference_available === true;
        const isManipulated = raw.prediction === 'likely_manipulated';
        const isInconclusive = raw.prediction === 'inconclusive';
        const isManipulationModel = ['faceforensicspp', 'forgerynet'].includes(raw.checkpoint_task);
        result = {
          id: `srv-${Date.now().toString(36)}-${Math.random().toString(36).substring(2, 6)}`,
          timestamp: new Date().toISOString(),
          processingTimeMs: null,
          isDemo: false,
          isDiagnostic: !inferenceAvailable,
          disclaimer: inferenceAvailable
            ? isManipulationModel
              ? 'FACEFORENSICS++ RGB MODEL — MANIPULATED VS REAL'
              : 'AI-GENERATED VS REAL MODEL — UNCALIBRATED OUTPUT'
            : 'DIAGNOSTIC OUTPUT — NOT A VALIDATED MODEL PREDICTION',
          verdict: inferenceAvailable
            ? (isInconclusive ? 'Inconclusive' : (isManipulated ? 'Likely Manipulated' : 'Likely Real'))
            : 'Diagnostic inspection complete',
          isManipulated: inferenceAvailable && !isInconclusive ? isManipulated : null,
          isInconclusive,
          confidencePct: inferenceAvailable && typeof raw.score === 'number' ? raw.score * 100 : null,
          realProbabilityPct:
            inferenceAvailable && typeof raw.real_probability === 'number'
              ? raw.real_probability * 100
              : null,
          fakeProbabilityPct:
            inferenceAvailable && typeof raw.fake_probability === 'number'
              ? raw.fake_probability * 100
              : null,
          scoreType: raw.score_type || 'No classifier score available',
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
          checkpointTask: raw.checkpoint_task,
          labelSemantics: raw.label_semantics,
          domainWarning: raw.domain_warning,
          status: raw.status,
          inferenceAvailable,
          diagnosticMessage: raw.message,
          verdictState: raw.verdict_state || (inferenceAvailable ? 'INCONCLUSIVE' : 'DIAGNOSTIC ONLY'),
          modelAgreement: raw.model_agreement || null,
          models: Array.isArray(raw.models) ? raw.models : [],
          modelAvailability: Array.isArray(raw.model_availability) ? raw.model_availability : [],
          detections: Array.isArray(raw.detections) ? raw.detections : [],
          extended: raw.extended || null,
          dwtLevels: raw.dwt_levels || {},
          // Separate detection channels
          separateDetections: raw.separate_detections || {
            deepfake_manipulation: {
              verdict: isManipulated ? 'Likely Manipulated' : (isInconclusive ? 'Inconclusive' : 'Likely Authentic'),
              task: 'deepfake_manipulation_vs_authentic',
              labelSemantics: 'Manipulated versus authentic',
            },
            ai_generation: {
              verdict: 'Inconclusive (Requires 32x32 native image)',
              task: 'ai_generated_vs_real',
              labelSemantics: 'AI-generated versus real',
            },
          },
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
