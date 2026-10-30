import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import PageLayout from '../components/layout/PageLayout';
import PredictionBadge from '../components/common/PredictionBadge';
import ScoreCard from '../components/common/ScoreCard';
import EmptyState from '../components/common/EmptyState';
import FrequencySpectrumViewer from '../components/results/FrequencySpectrumViewer';
import WaveletViewer from '../components/results/WaveletViewer';
import SpectralChart from '../components/results/SpectralChart';
import AnalysisSummary from '../components/results/AnalysisSummary';
import ModelComparison from '../components/results/ModelComparison';
import ForensicImageViewer from '../components/results/ForensicImageViewer';
import RGBHistogram from '../components/results/RGBHistogram';
import FFTSpectrum from '../components/results/FFTSpectrum';
import ForensicEvidencePanels from '../components/results/ForensicEvidencePanels';
import DWTDecomposition from '../components/results/DWTDecomposition';
import FileMetadata from '../components/upload/FileMetadata';
import { analysisService } from '../services/analysisService';
import { reportService } from '../services/reportService';
import { formatDate } from '../utils/formatters';
import {
  Printer,
  FileDown,
  ArrowLeft,
  AlertTriangle,
  Clock,
  ShieldAlert,
  Info,
} from 'lucide-react';

export default function ResultsPage() {
  const { analysisId } = useParams();
  const navigate = useNavigate();

  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sourcePreviewFailed, setSourcePreviewFailed] = useState(false);

  useEffect(() => {
    setLoading(true);
    const record = analysisService.getAnalysisById(analysisId);
    setAnalysis(record);
    setSourcePreviewFailed(false);
    setLoading(false);
  }, [analysisId]);

  if (loading) {
    return (
      <PageLayout>
        <div className="py-24 text-center text-xs text-slate-400 font-mono flex flex-col items-center justify-center space-y-3">
          <div className="w-6 h-6 border-2 border-accent-cyan border-t-transparent rounded-full animate-spin" />
          <span>Loading forensic inspection record...</span>
        </div>
      </PageLayout>
    );
  }

  if (!analysis) {
    return (
      <PageLayout>
        <EmptyState
          title="Analysis Record Not Found"
          description={`No inspection result matching ID "${analysisId}" exists in local session history.`}
          actionText="Inspect New Image"
          onAction={() => navigate('/analyze')}
        />
      </PageLayout>
    );
  }

  const isDiagnostic =
    !analysis.inferenceAvailable || analysis.verdictState === 'NOT APPLICABLE';

  return (
    <PageLayout isDiagnostic={isDiagnostic}>
      <div className="space-y-8">
        {/* Navigation / Actions Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-4 no-print">
          <Link
            to="/analyze"
            className="inline-flex items-center space-x-1.5 text-xs text-slate-400 hover:text-slate-100 transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent-cyan rounded px-1.5 py-0.5"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Analyze Another Image</span>
          </Link>

          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={() => reportService.downloadTextSummary(analysis)}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-slate-100 bg-card hover:bg-card-hover border border-border rounded-md transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan"
            >
              <FileDown className="w-3.5 h-3.5" />
              <span>Download Text Summary</span>
            </button>
            <button
              type="button"
              onClick={() => reportService.printReport()}
              className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 text-xs font-semibold text-canvas bg-accent-cyan hover:bg-accent-cyan-light rounded-md shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan"
            >
              <Printer className="w-3.5 h-3.5" />
              <span>Print Report (PDF)</span>
            </button>
          </div>
        </div>

        {/* DEMO / DIAGNOSTIC NOTICE BANNER */}
        {(analysis.disclaimer || isDiagnostic || analysis.isDemo) && (
          <div
            role="status"
            className="bg-amber-950/30 border border-amber-800/60 rounded-xl p-4 flex items-start space-x-3 text-xs text-amber-300"
          >
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <span className="font-bold tracking-wide uppercase font-mono block text-amber-300">
                {analysis.disclaimer || 'DIAGNOSTIC OUTPUT — NOT A VALIDATED MODEL PREDICTION'}
              </span>
              <p className="text-amber-200/80 leading-relaxed text-[11px]">
                {analysis.diagnosticMessage ||
                  (isDiagnostic
                    ? 'This diagnostic inspection decomposes spatial RGB features and frequency spectra. No trained classifier or deepfake confidence score is computed in this diagnostic phase.'
                    : 'This result was produced by the client-side demonstration service for prototype workflow validation. It is not an actual model prediction.')}
              </p>
            </div>
          </div>
        )}

        {/* STATUS CARD: Diagnostic Only Badge OR Classification Verdict */}
        {isDiagnostic ? (
          <div className="rounded-2xl border border-amber-800/60 bg-card p-6 sm:p-8 shadow-xl space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border/60 pb-5">
              <div className="space-y-2">
                <span className="text-[10px] font-mono uppercase tracking-widest text-slate-400">
                  Forensic Pipeline Status
                </span>
                <div className="flex items-center space-x-3">
                  <span className="inline-flex items-center space-x-1.5 rounded-md border border-amber-700/80 bg-amber-950/40 px-3.5 py-1.5 text-xs font-bold text-amber-300 uppercase tracking-wider font-mono">
                    <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
                    <span>Diagnostic Only</span>
                  </span>
                  <span className="text-xs text-slate-400 font-mono">ID: {analysis.id}</span>
                </div>
              </div>

              <div className="text-left sm:text-right">
                <span className="text-[11px] text-slate-400 block font-mono">
                  Classifier Verdict
                </span>
                <span className="text-lg sm:text-xl font-bold font-mono text-slate-400">
                  Unavailable (Diagnostics Only)
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs text-slate-400 font-mono pt-1">
              <div className="flex items-center space-x-2">
                <Clock className="w-3.5 h-3.5 text-slate-500" />
                <span>Timestamp: {formatDate(analysis.timestamp)}</span>
              </div>
              <div>
                <span>Pipeline Latency: {analysis.processingTimeMs ? `${analysis.processingTimeMs} ms` : 'In-memory'}</span>
              </div>
              <div>
                <span>Score Type: {analysis.scoreType || 'No classifier score available'}</span>
              </div>
            </div>
          </div>
        ) : (
          <>
          {/* Dual Detection Results: Deepfake vs AI-Generated */}
          {analysis.separateDetections &&
            Object.keys(analysis.separateDetections).length > 0 &&
            !isDiagnostic && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Card 1: Deepfake (Manipulated) Detection */}
              <div className="rounded-xl border border-border bg-card p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="text-lg">🎭</span>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200 font-mono">
                      Deepfake / Manipulation
                    </h4>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                    FaceForensics++
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-canvas border border-border/50">
                  <div className="text-xs text-slate-400 font-mono">Verdict</div>
                  <div className="text-lg font-bold font-mono text-slate-100">
                    {analysis.separateDetections.deepfake_manipulation?.verdict || 'Analysis pending'}
                  </div>
                  <div className="text-[11px] text-slate-500 font-mono mt-1">
                    Detects face swaps, reenactments, and photographic manipulation
                  </div>
                </div>
                {typeof analysis.confidencePct === 'number' && (
                  <div className="flex justify-between items-center text-xs font-mono text-slate-400 pt-1">
                    <span>Manipulation Confidence:</span>
                    <span className="font-bold text-accent-cyan">{analysis.confidencePct.toFixed(1)}%</span>
                  </div>
                )}
              </div>

              {/* Card 2: AI-Generated (Synthetic) Detection */}
              <div className="rounded-xl border border-border bg-card p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="text-lg">🤖</span>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200 font-mono">
                      AI-Generated / Synthetic
                    </h4>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                    CIFAKE
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-canvas border border-border/50">
                  <div className="text-xs text-slate-400 font-mono">Verdict</div>
                  <div className="text-lg font-bold font-mono text-slate-100">
                    {analysis.separateDetections.ai_generation?.verdict || 'Unavailable'}
                  </div>
                  <div className="text-[11px] text-slate-500 font-mono mt-1">
                    Detects Stable Diffusion, DALL-E, Midjourney outputs
                  </div>
                </div>
                <div className="text-[11px] text-amber-400/80 font-mono">
                  ⚠️ Note: CIFAKE model is trained on 32x32 images. Results for higher resolutions are inconclusive.
                </div>
              </div>
            </div>
          )}

          {/* Classification card is displayed only when a real model ran. */}
          <div
            className={`rounded-2xl border p-6 sm:p-8 shadow-xl transition-colors ${
              analysis.isInconclusive
                ? 'bg-slate-800/30 border-slate-700/60'
                : analysis.isManipulated
                ? 'bg-red-950/20 border-red-900/60 shadow-red-950/20'
                : 'bg-emerald-950/20 border-emerald-900/60 shadow-emerald-950/20'
            }`}
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border/40 pb-5">
              <div className="space-y-2">
                <span className="text-[10px] font-mono uppercase tracking-widest text-slate-400">
                  Forensic Classification Verdict
                </span>
                <div className="flex items-center space-x-3">
                  <PredictionBadge
                    isManipulated={analysis.isManipulated}
                    isInconclusive={analysis.isInconclusive}
                    size="large"
                  />
                  <span className="text-xs text-slate-400 font-mono">ID: {analysis.id}</span>
                </div>
              </div>

              <div className="text-left sm:text-right">
                <span className="text-[11px] text-slate-400 block font-mono">
                  Fake Probability
                </span>
                <span className="text-xl sm:text-2xl font-extrabold font-mono text-accent-cyan">
                  {typeof analysis.confidencePct === 'number'
                    ? `${analysis.confidencePct.toFixed(1)}%`
                    : 'N/A'}
                </span>
              </div>
            </div>

            <div className="pt-4 grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs text-slate-400 font-mono">
              <div className="flex items-center space-x-2">
                <Clock className="w-3.5 h-3.5 text-slate-500" />
                <span>Timestamp: {formatDate(analysis.timestamp)}</span>
              </div>
              <div>
                <span>Latency: {analysis.processingTimeMs ? `${analysis.processingTimeMs} ms` : 'N/A'}</span>
              </div>
              <div>
                <span>Score Type: {analysis.scoreType || 'Model score'}</span>
              </div>
            </div>
            {(typeof analysis.realProbabilityPct === 'number' ||
              typeof analysis.fakeProbabilityPct === 'number') && (
              <div className="pt-3 flex flex-wrap gap-4 text-xs text-slate-400 font-mono">
                <span>Real: {analysis.realProbabilityPct?.toFixed(1) ?? 'N/A'}%</span>
                <span>Fake: {analysis.fakeProbabilityPct?.toFixed(1) ?? 'N/A'}%</span>
              </div>
            )}
          </div>
          </>
        )}

        {analysis.models?.length > 0 && (
          <ModelComparison
            models={analysis.models}
            agreement={analysis.modelAgreement}
            detections={analysis.detections}
          />
        )}

        <ForensicImageViewer visualizations={analysis.visualizations} />

        {analysis.extended && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
              <RGBHistogram
                data={analysis.extended.histogram}
                stats={analysis.extended.channel_stats}
                brightness={analysis.extended.brightness}
                contrast={analysis.extended.contrast}
              />
              <FFTSpectrum
                imageUrl={analysis.extended.visualizations?.fft_magnitude || analysis.visualizations?.fftSpectrumUrl}
                profile={analysis.spectralProfile}
                energy={analysis.extended.frequency_energy}
              />
            </div>
            <ForensicEvidencePanels extended={analysis.extended} />
            <DWTDecomposition
              levels={analysis.dwtLevels}
              fallbackUrl={analysis.visualizations?.dwtSubbandsUrl}
            />
          </div>
        )}

        {/* Feature Score Cards: ONLY shown when not diagnostic and scores exist */}
        {analysis.inferenceAvailable && analysis.scores && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <ScoreCard
              title="Spatial RGB Branch"
              score={analysis.scores?.rgbBranch}
              accent="blue"
              description="Evaluates localized pixel inconsistencies and edge-boundary gradients."
            />
            <ScoreCard
              title="2D Fourier (FFT) Branch"
              score={analysis.scores?.fftBranch}
              accent="cyan"
              description="Exposes periodic high-frequency checkerboard grid patterns."
            />
            <ScoreCard
              title="Wavelet (DWT) Branch"
              score={analysis.scores?.dwtBranch}
              accent="violet"
              description="Audits high-frequency noise distribution in diagonal (HH) subband."
            />
          </div>
        )}

        {/* Multi-Modal Forensic Visualizations Grid */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200 font-mono">
              Multi-Domain Forensic Inspection Canvas
            </h3>
            <span className="text-[11px] text-slate-400 font-mono">
              {isDiagnostic ? 'Diagnostic Decomposition' : 'Extracted Features'}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* 1. Original Image Preview */}
            <div className="bg-card rounded-xl border border-border p-4 space-y-3">
              <div className="flex items-center space-x-2">
                <span className="w-2 h-2 rounded-full bg-accent-blue" />
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200 font-mono">
                  Source Image Capture
                </h4>
              </div>
              <div className="relative rounded-lg overflow-hidden border border-border bg-canvas aspect-square flex items-center justify-center">
                {analysis.visualizations?.originalPreviewUrl && !sourcePreviewFailed ? (
                  <img
                    src={analysis.visualizations.originalPreviewUrl}
                    alt="Original Upload"
                    className="w-full h-full object-cover"
                    onError={() => setSourcePreviewFailed(true)}
                  />
                ) : (
                  <div className="text-xs text-slate-500 font-mono p-4 text-center">
                    Original image is not retained after this session for privacy.
                  </div>
                )}
              </div>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Source photograph used for this active inspection. It is not retained in browser history.
              </p>
            </div>

            {/* 2. FFT Spectrum Viewer */}
            <FrequencySpectrumViewer
              fftUrl={analysis.visualizations?.fftSpectrumUrl}
              isManipulated={Boolean(analysis.isManipulated)}
            />

            {/* 3. Wavelet Subbands Viewer */}
            <WaveletViewer
              dwtUrl={analysis.visualizations?.dwtSubbandsUrl}
            />
          </div>
        </div>

        {/* Radial Spectral Energy Curve & Summary */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <SpectralChart
            profileData={analysis.spectralProfile}
            isManipulated={Boolean(analysis.isManipulated)}
          />

          <AnalysisSummary
            findings={analysis.findings}
            modelVersion={analysis.modelVersion}
          />
        </div>

        {/* File Metadata Table */}
        {analysis.metadata && <FileMetadata metadata={analysis.metadata} />}

        {/* Scientific Context Disclaimer */}
        <div className="bg-card-subtle p-5 rounded-xl border border-border text-xs text-slate-400 space-y-2 leading-relaxed">
          <div className="flex items-center space-x-2 text-slate-300 font-semibold">
            <Info className="w-4 h-4 text-accent-cyan" />
            <span>Forensic Interpretation &amp; Technical Limitations</span>
          </div>
          <p>
            An FFT magnitude anomaly does not constitute conclusive proof of synthetic generation. Common photographic transforms—such as aggressive JPEG compression, downsampling, digital sharpening filters, and lens distortion—can also induce shifts in high-frequency spectral slopes. Forensic findings should be cross-examined with spatial Error-Level Analysis (ELA) and verified against original capture metadata.
          </p>
        </div>
      </div>
    </PageLayout>
  );
}
