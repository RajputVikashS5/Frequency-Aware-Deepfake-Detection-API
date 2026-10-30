import React from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

function percentage(value) {
  return typeof value === 'number' ? `${(value * 100).toFixed(1)}%` : 'Unavailable';
}

function DetectionGroup({ detection }) {
  const models = detection.models || [];
  const chartData = models
    .filter((model) => model.available)
    .map((model) => ({
      name: model.key.toUpperCase(),
      Real: typeof model.real_probability === 'number' ? model.real_probability * 100 : 0,
      Fake: typeof model.fake_probability === 'number' ? model.fake_probability * 100 : 0,
    }));

  return (
    <div className="space-y-4 rounded-xl border border-border bg-card-subtle p-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-100 font-mono">
            {detection.task === 'ai_generated_vs_real' ? 'AI-generated image detection' : 'Deepfake / manipulation detection'}
          </h4>
          <p className="text-[11px] text-slate-400 font-mono mt-1">{detection.label_semantics}</p>
        </div>
        <span className="text-xs font-bold uppercase text-slate-100 font-mono">{detection.verdict}</span>
      </div>
      <div className="flex flex-wrap gap-3 text-[10px] font-mono text-slate-400">
        <span>{detection.available ? 'Task model available' : 'Model unavailable'}</span>
        <span>{detection.model_agreement ? `Models ${detection.model_agreement}` : 'Agreement unavailable'}</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {models.map((model) => (
          <article key={model.key} className="rounded-xl border border-border bg-card p-4 space-y-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-100 font-mono">{model.name}</h4>
                <p className="text-[10px] text-slate-500 font-mono mt-1">{model.task || 'Task unavailable'}</p>
              </div>
              <span className={`text-[10px] font-mono uppercase ${model.available ? 'text-emerald-400' : 'text-amber-300'}`}>
                {model.available ? 'Available' : 'Unavailable'}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs font-mono">
              <div><span className="block text-slate-500">Real</span><span className="text-slate-200">{percentage(model.real_probability)}</span></div>
              <div><span className="block text-slate-500">Fake</span><span className="text-slate-200">{percentage(model.fake_probability)}</span></div>
            </div>
            <div className="text-[10px] text-slate-500 font-mono space-y-1">
              <p>Prediction: <span className="text-slate-300">{model.prediction || 'Model unavailable'}</span></p>
              <p>Calibration: <span className={model.calibrated ? 'text-emerald-400' : 'text-amber-300'}>{model.calibrated ? (model.calibration_method || 'Calibrated') : 'Uncalibrated'}</span></p>
              <p>Latency: <span className="text-slate-300">{typeof model.processing_time_ms === 'number' ? `${model.processing_time_ms} ms` : 'N/A'}</span></p>
              <p>Checkpoint: <span className="text-slate-300 break-all">{model.model_version || 'N/A'}</span></p>
            </div>
          </article>
        ))}
      </div>

      {detection.warning && <p className="text-[11px] text-amber-300">{detection.warning}</p>}

      {chartData.length > 0 && (
        <div className="rounded-xl border border-border bg-card p-4">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono mb-3">Real vs Fake Probability</h4>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f293d" />
                <XAxis dataKey="name" stroke="#94a3b8" tick={{ fontSize: 10 }} />
                <YAxis domain={[0, 100]} stroke="#94a3b8" tick={{ fontSize: 10 }} />
                <Tooltip formatter={(value) => `${Number(value).toFixed(1)}%`} />
                <Legend />
                <Bar dataKey="Real" fill="#22d3ee" radius={[3, 3, 0, 0]} />
                <Bar dataKey="Fake" fill="#a78bfa" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ModelComparison({ models = [], agreement, detections = [] }) {
  const groups = detections.length
    ? detections
    : [{
        task: 'deepfake_manipulation_vs_authentic',
        label_semantics: 'Manipulated versus authentic',
        verdict: agreement ? 'MODEL COMPARISON' : 'MODEL RESULTS',
        available: models.some((model) => model.available),
        model_agreement: agreement,
        models,
        warning: null,
      }];

  return (
    <section className="space-y-4" aria-labelledby="model-comparison-heading">
      <h3 id="model-comparison-heading" className="text-sm font-bold uppercase tracking-wider text-slate-200 font-mono">
        Independent detection tasks
      </h3>
      {groups.map((detection) => (
        <DetectionGroup key={detection.task} detection={detection} />
      ))}
    </section>
  );
}
