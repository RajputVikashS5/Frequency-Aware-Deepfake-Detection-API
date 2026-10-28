import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import PageLayout from '../components/layout/PageLayout';
import ImageDropzone from '../components/upload/ImageDropzone';
import ImagePreview from '../components/upload/ImagePreview';
import FileMetadata from '../components/upload/FileMetadata';
import ValidationMessage from '../components/upload/ValidationMessage';
import AnalysisProgress from '../components/upload/AnalysisProgress';
import ErrorState from '../components/common/ErrorState';
import {
  validateFile,
  validateImageDecoding,
  safeRevokeUrl,
  readImageForSession,
} from '../utils/fileValidation';
import { analysisService } from '../services/analysisService';
import { appConfig } from '../config/appConfig';
import { Shield, Lock, Play, ArrowRight, Sparkles } from 'lucide-react';

export default function AnalyzePage() {
  const navigate = useNavigate();

  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [dimensions, setDimensions] = useState(null);
  const [validationError, setValidationError] = useState(null);
  const [isValidating, setIsValidating] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState(null);

  // File selection and validation
  const handleFile = async (file) => {
    // Revoke prior URL
    if (previewUrl) {
      safeRevokeUrl(previewUrl);
    }

    setValidationError(null);
    setAnalysisError(null);
    setSelectedFile(null);
    setPreviewUrl(null);
    setDimensions(null);

    // 1. Basic validation (size, MIME, extension)
    const basicCheck = validateFile(file);
    if (!basicCheck.isValid) {
      setValidationError(basicCheck.error);
      return;
    }

    // 2. Image decoding check
    setIsValidating(true);
    const objectUrl = URL.createObjectURL(file);
    const decodeCheck = await validateImageDecoding(file);
    setIsValidating(false);

    if (!decodeCheck.isValid) {
      URL.revokeObjectURL(objectUrl);
      setValidationError(decodeCheck.error);
      return;
    }

    setSelectedFile(file);
    setPreviewUrl(objectUrl);
    setDimensions({ width: decodeCheck.width, height: decodeCheck.height });
  };

  const handleRemove = () => {
    if (previewUrl) {
      safeRevokeUrl(previewUrl);
    }
    setSelectedFile(null);
    setPreviewUrl(null);
    setDimensions(null);
    setValidationError(null);
    setAnalysisError(null);
  };

  const handleStartAnalysis = async () => {
    if (!selectedFile || !previewUrl || isAnalyzing) return;

    setIsAnalyzing(true);
    setAnalysisError(null);

    try {
      // Use an in-memory data URL for the active Results page. This is not
      // persisted to history, so refreshes and older records keep the privacy
      // boundary while the live result always has a displayable source image.
      const sessionPreviewUrl = await readImageForSession(selectedFile);
      const result = await analysisService.analyzeImage(selectedFile, sessionPreviewUrl);
      // Navigate to Results page with the analysis ID
      navigate(`/results/${result.id}`);
    } catch (err) {
      console.error('Analysis execution failed:', err);
      setAnalysisError(err.message || 'Inspection pipeline failed. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <PageLayout maxWidth="max-w-4xl">
      <div className="space-y-8">
        {/* Header */}
        <div className="border-b border-border pb-4">
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight">
            Analyze Facial Photograph
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">
            Upload an uncompressed or standard resolution facial image. The forensic pipeline validates file integrity and extracts spatial, Fourier (FFT), and wavelet features.
          </p>
        </div>

        {/* Validation Error Banner */}
        {validationError && (
          <ValidationMessage message={validationError} />
        )}

        {/* Analysis Failure Banner */}
        {analysisError && (
          <ErrorState
            message={analysisError}
            onRetry={handleStartAnalysis}
          />
        )}

        {/* In-Flight Analysis Progress */}
        {isAnalyzing && (
          <AnalysisProgress />
        )}

        {/* Main Upload / Preview Area */}
        {!isAnalyzing && (
          <div className="space-y-6">
            {!selectedFile ? (
              <ImageDropzone
                onFileSelected={handleFile}
                onError={(msg) => setValidationError(msg)}
              />
            ) : (
              <div className="space-y-4">
                <ImagePreview
                  file={selectedFile}
                  previewUrl={previewUrl}
                  dimensions={dimensions}
                  onRemove={handleRemove}
                  onReplace={() => handleRemove()}
                />

                <FileMetadata
                  metadata={{
                    filename: selectedFile.name,
                    fileSize: selectedFile.size,
                    width: dimensions?.width,
                    height: dimensions?.height,
                  }}
                />

                {/* Explicit Analyze Action */}
                <div className="flex items-center justify-between pt-2">
                  <button
                    type="button"
                    onClick={handleRemove}
                    className="text-xs text-slate-400 hover:text-slate-200 transition-colors"
                  >
                    Cancel and select another image
                  </button>

                  <button
                    type="button"
                    onClick={handleStartAnalysis}
                    disabled={!selectedFile || isValidating}
                    className="inline-flex items-center space-x-2 px-6 py-2.5 rounded-lg text-xs font-semibold text-canvas bg-accent-cyan hover:bg-accent-cyan-light shadow-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <span>Analyze Image</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Privacy Notice */}
        <div className="bg-card-subtle p-4 rounded-xl border border-border flex items-start space-x-3 text-xs text-slate-400">
          <Lock className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-semibold text-slate-300 block">Privacy Notice</span>
            <p className="leading-relaxed">
              {appConfig.disclaimers.privacyNotice} Image files are processed strictly in-memory. In Demo Mode, calculations and frequency visualizations execute locally within your browser sandbox.
            </p>
          </div>
        </div>
      </div>
    </PageLayout>
  );
}
