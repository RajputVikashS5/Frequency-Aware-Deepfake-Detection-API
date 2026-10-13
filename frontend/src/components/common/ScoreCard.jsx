import React from 'react';

export default function ScoreCard({ title, score, description, accent = 'cyan' }) {
  const accentColors = {
    cyan: { text: 'text-accent-cyan', bar: 'bg-accent-cyan', border: 'border-accent-cyan/30' },
    blue: { text: 'text-accent-blue', bar: 'bg-accent-blue', border: 'border-accent-blue/30' },
    violet: { text: 'text-accent-violet', bar: 'bg-accent-violet', border: 'border-accent-violet/30' },
  };

  const style = accentColors[accent] || accentColors.cyan;
  const numScore = Number(score) || 0;

  return (
    <div className="bg-card p-4 rounded-lg border border-border space-y-2">
      <div className="flex justify-between items-center text-xs">
        <span className="font-medium text-slate-300">{title}</span>
        <span className={`font-mono font-bold text-sm ${style.text}`}>
          {numScore.toFixed(1)}%
        </span>
      </div>

      <div className="w-full bg-canvas rounded-full h-1.5 overflow-hidden border border-border-muted">
        <div
          className={`h-full ${style.bar} transition-all duration-700`}
          style={{ width: `${Math.min(100, Math.max(0, numScore))}%` }}
        />
      </div>

      {description && (
        <p className="text-[11px] text-slate-400 leading-tight">
          {description}
        </p>
      )}
    </div>
  );
}
