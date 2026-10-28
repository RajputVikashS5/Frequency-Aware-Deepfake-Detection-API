import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import ResultsPage from './ResultsPage';
import { analysisService } from '../services/analysisService';

describe('ResultsPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders diagnostic inspection result: displays diagnostic banner and hides classification card', () => {
    const mockDiagnosticResult = {
      id: 'diag-test-456',
      timestamp: '2026-10-28T12:00:00.000Z',
      processingTimeMs: 850,
      isDemo: false,
      isDiagnostic: true,
      disclaimer: 'DIAGNOSTIC OUTPUT — NOT A VALIDATED MODEL PREDICTION',
      diagnosticMessage: 'Multi-modal diagnostic extraction completed successfully.',
      isManipulated: null,
      confidencePct: null,
      scores: null,
      scoreType: 'No classifier score available',
      metadata: {
        filename: 'evidence_01.jpg',
        fileSize: 204800,
        mimeType: 'image/jpeg',
      },
      visualizations: {
        originalPreviewUrl: 'blob:http://localhost/test',
        fftSpectrumUrl: 'data:image/jpeg;base64,mockFFT',
        dwtSubbandsUrl: 'data:image/jpeg;base64,mockDWT',
      },
      spectralProfile: [
        { frequency: '0.1π', energy: 80, idealReference: 80 },
      ],
      findings: [
        'Radial log-magnitude spectrum shows characteristic synthetic high-frequency elevation.',
        'Haar diagonal HH subband confirms high-frequency noise discrepancy.',
      ],
      modelVersion: 'ResNet18-FFT-DWT-v1.0-diag',
    };

    vi.spyOn(analysisService, 'getAnalysisById').mockReturnValue(mockDiagnosticResult);

    render(
      <MemoryRouter initialEntries={['/results/diag-test-456']}>
        <Routes>
          <Route path="/results/:analysisId" element={<ResultsPage />} />
        </Routes>
      </MemoryRouter>
    );

    // 1. Diagnostic Banner is present
    expect(
      screen.getByText(/diagnostic output — not a validated model prediction/i)
    ).toBeInTheDocument();

    // 2. Diagnostic Only badge is rendered
    expect(screen.getByText(/diagnostic only/i)).toBeInTheDocument();
    expect(screen.getByText(/unavailable \(diagnostics only\)/i)).toBeInTheDocument();

    // 3. Classification verdict card and score cards must NOT be rendered
    expect(screen.queryByText(/forensic classification verdict/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/likely manipulated/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/likely real/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/spatial rgb branch/i)).not.toBeInTheDocument();

    // 4. Multi-modal visualization canvas & summary are present
    expect(screen.getByText(/multi-domain forensic inspection canvas/i)).toBeInTheDocument();
    expect(screen.getByText(/diagnostic evidence summary/i)).toBeInTheDocument();
    expect(
      screen.getByText(/radial log-magnitude spectrum shows characteristic synthetic/i)
    ).toBeInTheDocument();
  });

  it('renders classification card and score cards when analysis is not diagnostic (demo mode)', () => {
    const mockDemoResult = {
      id: 'demo-test-789',
      timestamp: '2026-10-28T12:00:00.000Z',
      processingTimeMs: 1200,
      isDemo: true,
      isDiagnostic: false,
      disclaimer: 'DEMO DATA — NOT AN ACTUAL MODEL PREDICTION',
      isManipulated: true,
      confidencePct: 88.6,
      scoreType: 'Calibrated Multimodal Fusion Probability',
      scores: {
        rgbBranch: 74.2,
        fftBranch: 93.4,
        dwtBranch: 86.5,
        fusedModel: 88.6,
      },
      metadata: {
        filename: 'demo_face.jpg',
        fileSize: 102400,
      },
      visualizations: {
        originalPreviewUrl: 'blob:http://localhost/demo',
        fftSpectrumUrl: 'data:image/jpeg;base64,demoFFT',
        dwtSubbandsUrl: 'data:image/jpeg;base64,demoDWT',
      },
      spectralProfile: [],
      findings: ['Demo finding'],
      modelVersion: 'ResNet18-FFT-DWT-v1.0 (Demo Scaffold)',
    };

    vi.spyOn(analysisService, 'getAnalysisById').mockReturnValue(mockDemoResult);

    render(
      <MemoryRouter initialEntries={['/results/demo-test-789']}>
        <Routes>
          <Route path="/results/:analysisId" element={<ResultsPage />} />
        </Routes>
      </MemoryRouter>
    );

    // Classification Verdict card and score cards should be rendered
    expect(screen.getByText(/forensic classification verdict/i)).toBeInTheDocument();
    expect(screen.getByText(/likely manipulated/i)).toBeInTheDocument();
    expect(screen.getByText(/88.6%/i)).toBeInTheDocument();
    expect(screen.getByText(/spatial rgb branch/i)).toBeInTheDocument();
    expect(screen.getByText(/2d fourier \(fft\) branch/i)).toBeInTheDocument();
    expect(screen.getByText(/wavelet \(dwt\) branch/i)).toBeInTheDocument();
  });

  it('shows empty state when analysis record is not found', () => {
    vi.spyOn(analysisService, 'getAnalysisById').mockReturnValue(null);

    render(
      <MemoryRouter initialEntries={['/results/nonexistent-id']}>
        <Routes>
          <Route path="/results/:analysisId" element={<ResultsPage />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText(/analysis record not found/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /inspect new image/i })).toBeInTheDocument();
  });

  it('explains why the source image is unavailable for a retained history record', () => {
    vi.spyOn(analysisService, 'getAnalysisById').mockReturnValue({
      id: 'history-test-123',
      timestamp: '2026-10-28T12:00:00.000Z',
      isDiagnostic: true,
      metadata: { filename: 'private-image.jpg', fileSize: 128 },
      visualizations: {},
      findings: [],
      spectralProfile: [],
    });

    render(
      <MemoryRouter initialEntries={['/results/history-test-123']}>
        <Routes>
          <Route path="/results/:analysisId" element={<ResultsPage />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText(/original image is not retained after this session for privacy/i)).toBeInTheDocument();
  });
});
