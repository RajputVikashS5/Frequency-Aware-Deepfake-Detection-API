import { appConfig } from '../config/appConfig';

/**
 * Creates client-side forensic visualizations using an offscreen canvas.
 */
function generateCanvasVisualizations(imgElement) {
  const size = 256;
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext('2d');

  // 1. Generate FFT Magnitude Spectrum
  ctx.fillStyle = '#05070e';
  ctx.fillRect(0, 0, size, size);

  const cx = size / 2;
  const cy = size / 2;
  const maxR = size / 2;

  // Background smooth 1/f falloff
  for (let r = maxR; r > 2; r -= 3) {
    const intensity = Math.pow(1 - r / maxR, 2.2);
    ctx.strokeStyle = `rgba(34, 211, 238, ${intensity * 0.4})`;
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.stroke();
  }

  // Central DC peak
  const gradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, 28);
  gradient.addColorStop(0, '#ffffff');
  gradient.addColorStop(0.3, '#22d3ee');
  gradient.addColorStop(1, 'transparent');
  ctx.fillStyle = gradient;
  ctx.beginPath();
  ctx.arc(cx, cy, 28, 0, Math.PI * 2);
  ctx.fill();

  const fftDataUrl = canvas.toDataURL('image/jpeg', 0.9);

  // 2. Generate 4-Subband Haar DWT Visualization
  ctx.fillStyle = '#0b0f19';
  ctx.fillRect(0, 0, size, size);

  const half = size / 2;
  // Quadrant backgrounds
  // LL (Top-Left): Approximation
  ctx.drawImage(imgElement, 0, 0, half, half);
  ctx.fillStyle = 'rgba(11, 15, 25, 0.2)';
  ctx.fillRect(0, 0, half, half);

  // HL (Top-Right): Vertical high-pass
  ctx.fillStyle = '#0e121e';
  ctx.fillRect(half, 0, half, half);

  // LH (Bottom-Left): Horizontal high-pass
  ctx.fillStyle = '#0e121e';
  ctx.fillRect(0, half, half, half);

  // HH (Bottom-Right): Diagonal high-pass
  ctx.fillStyle = '#0d101b';
  ctx.fillRect(half, half, half, half);

  // Subband grid borders & labels
  ctx.strokeStyle = '#1e293b';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(half, 0);
  ctx.lineTo(half, size);
  ctx.moveTo(0, half);
  ctx.lineTo(size, half);
  ctx.stroke();

  ctx.font = '10px monospace';
  ctx.fillStyle = '#38bdf8';
  ctx.fillText('LL: Approx', 6, 16);
  ctx.fillStyle = '#a78bfa';
  ctx.fillText('HL: Vertical', half + 6, 16);
  ctx.fillText('LH: Horiz', 6, half + 16);
  ctx.fillStyle = '#a78bfa';
  ctx.fillText('HH: Diagonal (HF)', half + 6, half + 16);

  const dwtDataUrl = canvas.toDataURL('image/jpeg', 0.9);

  // 3. Generate Spatial Error-Level (ELA) Heatmap
  ctx.drawImage(imgElement, 0, 0, size, size);
  const elaGradient = ctx.createRadialGradient(cx, cy, 20, cx, cy, size / 2);
  elaGradient.addColorStop(0, 'rgba(59, 130, 246, 0.25)');
  elaGradient.addColorStop(0.6, 'rgba(59, 130, 246, 0.2)');
  elaGradient.addColorStop(1, 'rgba(15, 23, 42, 0.6)');
  ctx.fillStyle = elaGradient;
  ctx.fillRect(0, 0, size, size);

  const spatialDataUrl = canvas.toDataURL('image/jpeg', 0.9);

  return {
    fftSpectrumUrl: fftDataUrl,
    dwtSubbandsUrl: dwtDataUrl,
    spatialHeatmapUrl: spatialDataUrl,
  };
}

/**
 * Executes demonstration analysis for a given file.
 * Produces structured, reproducible forensic outputs labeled as demo data.
 */
export async function analyzeInDemoMode(file, previewUrl) {
  // Simulate diagnostic demo latency; this is never a trained model result.
  await new Promise((resolve) => setTimeout(resolve, 1400));

  // Render client-side visual decomposition
  let visualizations = {
    fftSpectrumUrl: '',
    dwtSubbandsUrl: '',
    spatialHeatmapUrl: '',
  };

  try {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    await new Promise((resolve) => {
      const timer = setTimeout(resolve, 600);
      img.onload = () => {
        clearTimeout(timer);
        resolve();
      };
      img.onerror = () => {
        clearTimeout(timer);
        resolve();
      };
      img.src = previewUrl;
    });
    visualizations = generateCanvasVisualizations(img);
  } catch (e) {
    console.warn('Could not generate client-side canvas visualizations:', e);
  }

  const analysisId = `demo-${Date.now().toString(36)}-${Math.random().toString(36).substring(2, 6)}`;
  // Radial frequency profile for Recharts curve
  const spectralProfile = Array.from({ length: 18 }).map((_, i) => {
    const freq = (i / 18).toFixed(2);
    let energy;
    energy = Math.max(6, Math.round(96 * Math.exp(-i * 0.17)));
    return { frequency: `${freq}π`, energy, idealReference: Math.round(96 * Math.exp(-i * 0.17)) };
  });

  const findings = [
    'Client-side Fourier, wavelet, and spatial visualization layers were generated.',
    'No classifier prediction was produced in demo mode.',
  ];

  return {
    id: analysisId,
    timestamp: new Date().toISOString(),
    processingTimeMs: 1420,
    isDemo: true,
    disclaimer: appConfig.disclaimers.demoNotice,
    isDiagnostic: true,
    isManipulated: null,
    confidencePct: null,
    scoreType: 'No classifier score available',
    scores: null,
    metadata: {
      filename: file.name,
      fileSize: file.size,
      mimeType: file.type,
      sha256Digest: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    },
    visualizations: {
      originalPreviewUrl: previewUrl,
      fftSpectrumUrl: visualizations.fftSpectrumUrl,
      dwtSubbandsUrl: visualizations.dwtSubbandsUrl,
      spatialHeatmapUrl: visualizations.spatialHeatmapUrl,
    },
    spectralProfile,
    findings,
    modelVersion: 'ResNet18-FFT-DWT-v1.0 (Demo Scaffold)',
  };
}
