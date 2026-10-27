import React, { useState, useRef } from 'react';

export default function Detector() {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [results, setResults] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const handleSelectFile = (selected) => {
    if (!selected) return;
    if (!selected.type.startsWith('image/')) {
      setErrorMsg('Please select a valid image file (JPEG, PNG, WEBP, or BMP).');
      return;
    }
    setErrorMsg(null);
    setFile(selected);
    setPreviewUrl(URL.createObjectURL(selected));
    setResults(null);
  };

  const onDragOver = (e) => {
    e.preventDefault();
    setDragActive(true);
  };

  const onDragLeave = () => {
    setDragActive(false);
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleSelectFile(e.dataTransfer.files[0]);
    }
  };

  const runAnalysis = async () => {
    if (!file) return;
    setIsProcessing(true);
    setErrorMsg(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/api/v1/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server returned status ${response.status}`);
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      console.error('Inspection request failed:', err);
      setErrorMsg(
        'Unable to connect to the backend API at http://localhost:8000. Ensure the FastAPI server is running.'
      );
    } finally {
      setIsProcessing(false);
    }
  };

  const resetSelection = () => {
    setFile(null);
    setPreviewUrl(null);
    setResults(null);
    setErrorMsg(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
          Image Deepfake Inspection
        </h1>
        <p className="text-sm text-slate-600 mt-1 max-w-3xl leading-relaxed">
          Analyzes uploaded facial photographs by combining spatial evidence, 2D Fourier (FFT) log-magnitude spectrums, and Haar discrete wavelet (DWT) subband energy.
        </p>
      </div>

      {/* Upload Box */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-6 space-y-4">
        <div
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
            dragActive
              ? 'border-blue-600 bg-blue-50/50'
              : 'border-slate-300 hover:border-slate-400 bg-slate-50/50'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp,image/bmp"
            className="hidden"
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                handleSelectFile(e.target.files[0]);
              }
            }}
          />

          <div className="space-y-1">
            <p className="text-sm font-medium text-slate-800">
              {file ? file.name : 'Click to select an image, or drag and drop here'}
            </p>
            <p className="text-xs text-slate-500">
              Supported formats: JPEG, PNG, WEBP, BMP
            </p>
          </div>
        </div>

        {/* Selected file preview and action */}
        {file && (
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2 border-t border-slate-100">
            <div className="flex items-center space-x-3">
              {previewUrl && (
                <img
                  src={previewUrl}
                  alt="Preview"
                  className="w-12 h-12 rounded object-cover border border-slate-200"
                />
              )}
              <div className="text-xs">
                <span className="font-semibold text-slate-800 block truncate max-w-sm">
                  {file.name}
                </span>
                <span className="text-slate-500">
                  {(file.size / 1024).toFixed(1)} KB
                </span>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <button
                type="button"
                onClick={resetSelection}
                disabled={isProcessing}
                className="px-3 py-1.5 text-xs font-medium text-slate-600 hover:text-slate-900 border border-slate-200 rounded hover:bg-slate-50 disabled:opacity-50"
              >
                Clear
              </button>
              <button
                type="button"
                onClick={runAnalysis}
                disabled={isProcessing}
                className="px-5 py-2 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-800 rounded shadow-sm disabled:opacity-50"
              >
                {isProcessing ? 'Analyzing...' : 'Run Forensic Analysis'}
              </button>
            </div>
          </div>
        )}

        {/* Error message */}
        {errorMsg && (
          <div className="p-3 rounded border border-red-200 bg-red-50 text-red-800 text-xs">
            {errorMsg}
          </div>
        )}
      </div>

      {/* Loading state */}
      {isProcessing && (
        <div className="bg-white border border-slate-200 rounded-lg p-6 text-center text-sm text-slate-600 shadow-sm">
          Processing image: isolating face crop, computing 2D FFT, and decomposing wavelet subbands...
        </div>
      )}

      {/* Results View */}
      {results && !isProcessing && (
        <div className="space-y-6">
          {/* High-contrast Verdict banner */}
          <div className="rounded-lg border border-amber-300 bg-amber-50/80 p-6 text-amber-950">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b pb-4 mb-4 border-current/15">
              <div>
                <span className="text-xs uppercase font-mono font-bold tracking-wider opacity-75">
                  Diagnostic Status — Not a Model Prediction
                </span>
                <h2 className="text-2xl font-bold tracking-tight">
                  {results.status === 'diagnostic_complete' ? 'Diagnostic inspection complete' : 'Unavailable'}
                </h2>
              </div>
              <div className="text-left sm:text-right">
                <span className="text-xs opacity-75 block">Classifier prediction</span>
                <span className="text-xl font-extrabold font-mono">Unavailable</span>
              </div>
            </div>

            {/* Findings list */}
            <div className="space-y-1.5 text-xs">
              <p className="font-semibold">{results.message}</p>
              <span className="font-semibold block opacity-90">Analysis Summary:</span>
              <ul className="list-disc list-inside space-y-1 pl-1">
                {results.findings.map((f, i) => (
                  <li key={i}>{f}</li>
                ))}
              </ul>
            </div>
          </div>

          {/* Forensic Decomposition Cards (4 Cards) */}
          <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-6 space-y-4">
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
              Multi-Modal Forensic Decomposition
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* 1. Face Crop */}
              <div className="border border-slate-200 rounded-md p-3 space-y-2 bg-slate-50/50">
                <span className="text-xs font-semibold text-slate-800 block">
                  1. Aligned Face Crop
                </span>
                <img
                  src={results.visualizations.face_crop}
                  alt="Face Crop"
                  className="w-full aspect-square object-cover rounded border border-slate-200 bg-white"
                />
                <p className="text-[11px] text-slate-500 leading-tight">
                  Normalized facial region cropped using OpenCV Haar cascade.
                </p>
              </div>

              {/* 2. FFT Spectrum */}
              <div className="border border-slate-200 rounded-md p-3 space-y-2 bg-slate-50/50">
                <span className="text-xs font-semibold text-slate-800 block">
                  2. 2D Fourier (FFT)
                </span>
                <img
                  src={results.visualizations.fft_spectrum}
                  alt="2D FFT"
                  className="w-full aspect-square object-cover rounded border border-slate-200 bg-white"
                />
                <p className="text-[11px] text-slate-500 leading-tight">
                  Centered log-magnitude spectrum. Highlights periodic grid spikes.
                </p>
              </div>

              {/* 3. DWT Wavelets */}
              <div className="border border-slate-200 rounded-md p-3 space-y-2 bg-slate-50/50">
                <span className="text-xs font-semibold text-slate-800 block">
                  3. Haar Wavelets (DWT)
                </span>
                <img
                  src={results.visualizations.dwt_subbands}
                  alt="DWT Subbands"
                  className="w-full aspect-square object-cover rounded border border-slate-200 bg-white"
                />
                <p className="text-[11px] text-slate-500 leading-tight">
                  4-subband decomposition: LL, HL (vert), LH (horiz), HH (diag).
                </p>
              </div>

              {/* 4. Spatial ELA */}
              <div className="border border-slate-200 rounded-md p-3 space-y-2 bg-slate-50/50">
                <span className="text-xs font-semibold text-slate-800 block">
                  4. Spatial ELA & Edges
                </span>
                <img
                  src={results.visualizations.spatial_heatmap}
                  alt="Spatial Heatmap"
                  className="w-full aspect-square object-cover rounded border border-slate-200 bg-white"
                />
                <p className="text-[11px] text-slate-500 leading-tight">
                  Error Level Analysis and boundary gradient overlay.
                </p>
              </div>
            </div>
          </div>

          {/* Diagnostic note & Image Metadata */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* No classification scores are exposed before Phase B. */}
            <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-6 space-y-3">
              <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide">Classifier Status</h3>
              <p className="text-xs leading-relaxed text-slate-600">
                This response contains diagnostic visualizations only. No real/fake verdict,
                confidence, calibrated probability, or trained model score is available.
              </p>
            </div>

            {/* Technical Metadata */}
            <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-6 space-y-3">
              <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
                Image Metadata & Integrity
              </h3>
              <table className="w-full text-xs text-left">
                <tbody className="divide-y divide-slate-100 text-slate-600">
                  <tr>
                    <td className="py-1.5 font-medium text-slate-800">File Name</td>
                    <td className="py-1.5 font-mono truncate max-w-xs">{results.metadata.filename}</td>
                  </tr>
                  <tr>
                    <td className="py-1.5 font-medium text-slate-800">Dimensions</td>
                    <td className="py-1.5 font-mono">{results.metadata.dimensions}</td>
                  </tr>
                  <tr>
                    <td className="py-1.5 font-medium text-slate-800">File Size</td>
                    <td className="py-1.5 font-mono">{results.metadata.filesize_kb} KB</td>
                  </tr>
                  <tr>
                    <td className="py-1.5 font-medium text-slate-800">Face Detected</td>
                    <td className="py-1.5 font-mono">
                      {results.metadata.face_detected ? 'Yes (Haar cascade)' : 'Center crop fallback'}
                    </td>
                  </tr>
                  <tr>
                    <td className="py-1.5 font-medium text-slate-800">SHA-256</td>
                    <td className="py-1.5 font-mono truncate max-w-xs" title={results.metadata.sha256}>
                      {results.metadata.sha256.slice(0, 24)}...
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Scientific Disclaimer from README */}
          <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 text-xs text-slate-600 leading-relaxed space-y-1">
            <span className="font-semibold text-slate-800 block">Methodological Note & Responsible Use:</span>
            <p>
              This diagnostic output is not a deepfake classification. Frequency-domain artifacts vary depending on the generation pipeline, compression rate, and resolution scaling. A trained and calibrated model will be evaluated only in a later phase.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
