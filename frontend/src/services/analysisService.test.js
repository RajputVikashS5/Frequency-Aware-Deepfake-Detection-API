import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { analysisService } from './analysisService';
import { apiClient } from './api';
import { appConfig } from '../config/appConfig';

describe('analysisService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('correctly maps backend diagnostic API responses when demo mode is disabled', async () => {
    // Temporarily disable demo mode
    const prevDemoMode = appConfig.isDemoMode;
    appConfig.isDemoMode = false;

    const mockDiagnosticApiResponse = {
      status: 'diagnostic_complete',
      message: 'Multi-modal diagnostic extraction completed successfully.',
      model_version: 'ResNet18-FFT-DWT-v1.0-diag',
      inference_available: false,
      metadata: {
        filename: 'suspect_face.jpg',
        filesize_kb: 412,
        dimensions: '512x512',
        face_detected: true,
        sha256: 'a1b2c3d4e5f67890abcdef1234567890',
      },
      visualizations: {
        face_crop: 'data:image/jpeg;base64,mockFaceCrop',
        fft_spectrum: 'data:image/jpeg;base64,mockFFTSpectrum',
        dwt_subbands: 'data:image/jpeg;base64,mockDWTSubbands',
        spatial_heatmap: 'data:image/jpeg;base64,mockELA',
      },
      spectral_profile: [
        { frequency: '0.1π', energy: 88, idealReference: 88 },
        { frequency: '0.5π', energy: 45, idealReference: 40 },
      ],
      findings: [
        'Radial frequency energy profile displays elevated mid-frequency harmonics.',
        'Haar diagonal HH subband residue exhibits synthetic upsampling discrepancies.',
      ],
    };

    const postSpy = vi.spyOn(apiClient, 'post').mockResolvedValue({
      data: mockDiagnosticApiResponse,
    });

    const file = new File(['mock content'], 'suspect_face.jpg', { type: 'image/jpeg' });
    const previewUrl = 'blob:http://localhost/mock-preview';

    const result = await analysisService.analyzeImage(file, previewUrl);

    expect(postSpy).toHaveBeenCalledWith('/api/v1/analyze', expect.any(FormData), expect.any(Object));

    // Verify diagnostic shape conforms to UI expectations
    expect(result.isDiagnostic).toBe(true);
    expect(result.isManipulated).toBeNull();
    expect(result.confidencePct).toBeNull();
    expect(result.scores).toBeNull();
    expect(result.disclaimer).toBe('DIAGNOSTIC OUTPUT — NOT A VALIDATED MODEL PREDICTION');
    expect(result.diagnosticMessage).toBe('Multi-modal diagnostic extraction completed successfully.');
    expect(result.findings).toHaveLength(2);
    expect(result.visualizations.fftSpectrumUrl).toBe('data:image/jpeg;base64,mockFFTSpectrum');
    expect(result.visualizations.dwtSubbandsUrl).toBe('data:image/jpeg;base64,mockDWTSubbands');
    expect(result.visualizations.originalPreviewUrl).toBe(previewUrl);
    expect(result.metadata.filename).toBe('suspect_face.jpg');

    // Restore appConfig
    appConfig.isDemoMode = prevDemoMode;
  });

  it('runs demo service analysis when demo mode is enabled', async () => {
    const prevDemoMode = appConfig.isDemoMode;
    appConfig.isDemoMode = true;

    const file = new File(['mock content'], 'test_photo.jpg', { type: 'image/jpeg' });
    const previewUrl = 'blob:http://localhost/test-preview';

    const result = await analysisService.analyzeImage(file, previewUrl);

    expect(result.isDemo).toBe(true);
    expect(result.id).toMatch(/^demo-/);
    expect(result.visualizations.originalPreviewUrl).toBe(previewUrl);
    expect(result.findings.length).toBeGreaterThan(0);

    appConfig.isDemoMode = prevDemoMode;
  });
});
