import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
} from 'recharts';

export default function SpectralChart({ profileData, isManipulated }) {
  if (!profileData || profileData.length === 0) return null;

  return (
    <div className="bg-card rounded-xl border border-border p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200 font-mono">
          Radial Frequency Energy Falloff Curve (DC → Nyquist)
        </h4>
        <span className="text-[10px] text-slate-400 font-mono">
          Azimuthal Average
        </span>
      </div>

      <div className="h-48 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={profileData} margin={{ top: 5, right: 10, left: -25, bottom: 0 }}>
            <defs>
              <linearGradient id="energyGrad" x1="0" y1="0" x2="0" y2="1">
                <stop
                  offset="5%"
                  stopColor={isManipulated ? '#ef4444' : '#06b6d4'}
                  stopOpacity={0.4}
                />
                <stop
                  offset="95%"
                  stopColor={isManipulated ? '#ef4444' : '#06b6d4'}
                  stopOpacity={0.0}
                />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="frequency"
              stroke="#64748b"
              fontSize={10}
              tickLine={false}
              interval={2}
            />
            <YAxis stroke="#64748b" fontSize={10} tickLine={false} domain={[0, 100]} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#111827',
                borderColor: '#1f293d',
                borderRadius: '8px',
                fontSize: '11px',
                color: '#f8fafc',
              }}
            />
            <Area
              type="monotone"
              dataKey="energy"
              stroke={isManipulated ? '#f87171' : '#22d3ee'}
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#energyGrad)"
              name="Measured Energy"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <p className="text-[11px] text-slate-400 leading-relaxed">
        Compares measured frequency decay against natural optical 1/f power-law distribution. Anomalies at higher radial bins indicate potential synthetic generative upsampling.
      </p>
    </div>
  );
}
