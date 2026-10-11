import React from 'react';
import ReactDOM from 'react-dom/client';
import './styles.css';

function App() {
  return (
    <main className="app-shell">
      <section className="panel">
        <p className="eyebrow">Research prototype</p>
        <h1>Frequency-Aware Deepfake Detection</h1>
        <p className="subtitle">
          Upload a video to begin the inspection pipeline. The model and report generation are
          planned for the next implementation phases.
        </p>

        <div className="upload-box">
          <label htmlFor="video-upload" className="file-label">
            Select video
          </label>
          <input id="video-upload" type="file" accept="video/*" />
        </div>

        <div className="status-card">
          <h2>Current status</h2>
          <ul>
            <li>Backend health endpoint: ready</li>
            <li>Upload validation: planned</li>
            <li>Model inference: planned</li>
            <li>Report generation: planned</li>
          </ul>
        </div>
      </section>
    </main>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
