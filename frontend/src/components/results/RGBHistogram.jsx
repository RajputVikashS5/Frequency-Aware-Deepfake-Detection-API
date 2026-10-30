import React, { useState } from 'react';
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

export default function RGBHistogram({ data = [], stats = {}, brightness, contrast }) {
  const [channels, setChannels] = useState({ red: true, green: true, blue: true });
  if (!data.length) return <div className="text-xs text-slate-500 font-mono">RGB histogram unavailable.</div>;
  return (
    <section className="rounded-xl border border-border bg-card p-5 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200 font-mono">RGB Histogram</h3>
        <div className="flex gap-2 text-[10px] font-mono">
          {Object.keys(channels).map((channel) => (
            <label key={channel} className="flex items-center gap-1">
              <input type="checkbox" checked={channels[channel]} onChange={() => setChannels((value) => ({ ...value, [channel]: !value[channel] }))} />
              <span className={`capitalize ${channel === 'red' ? 'text-red-400' : channel === 'green' ? 'text-emerald-400' : 'text-blue-400'}`}>{channel}</span>
            </label>
          ))}
        </div>
      </div>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <XAxis dataKey="intensity" domain={[0, 255]} tick={{ fontSize: 10 }} stroke="#64748b" />
            <YAxis tick={{ fontSize: 10 }} stroke="#64748b" />
            <Tooltip />
            {channels.red && <Line type="monotone" dataKey="red" stroke="#ef4444" dot={false} strokeWidth={1.5} />}
            {channels.green && <Line type="monotone" dataKey="green" stroke="#22c55e" dot={false} strokeWidth={1.5} />}
            {channels.blue && <Line type="monotone" dataKey="blue" stroke="#3b82f6" dot={false} strokeWidth={1.5} />}
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-[10px] font-mono text-slate-400">
        {['red', 'green', 'blue'].map((channel) => <span key={channel}>{channel}: {stats[channel]?.mean ?? 'N/A'} ± {stats[channel]?.std ?? 'N/A'}</span>)}
        <span>Brightness: {brightness ?? 'N/A'}</span><span>Contrast: {contrast ?? 'N/A'}</span>
      </div>
    </section>
  );
}
