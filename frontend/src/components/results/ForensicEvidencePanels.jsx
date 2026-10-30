import React from 'react';

function ImagePanel({ title, description, url }) {
  return (
    <article className="rounded-xl border border-border bg-card p-3 space-y-2">
      <h4 className="text-[11px] font-bold uppercase tracking-wider text-slate-200 font-mono">{title}</h4>
      <div className="aspect-video rounded bg-canvas border border-border flex items-center justify-center overflow-hidden">
        {url ? <img src={url} alt={title} className="w-full h-full object-contain" /> : <span className="text-[10px] text-slate-500">Unavailable</span>}
      </div>
      <p className="text-[10px] text-slate-500 leading-relaxed">{description}</p>
    </article>
  );
}

export default function ForensicEvidencePanels({ extended }) {
  if (!extended) return null;
  const visualizations = extended.visualizations || {};
  const metrics = extended.metrics || {};
  return (
    <section className="space-y-4">
      <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200 font-mono">Measured Forensic Evidence</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <ImagePanel title="ELA grayscale" description={`JPEG quality ${metrics.ela_quality ?? 'N/A'}; measured recompression residual.`} url={visualizations.ela_grayscale} />
        <ImagePanel title="ELA heatmap" description="Enhanced JPEG recompression difference." url={visualizations.ela_heatmap} />
        <ImagePanel title="Noise residual" description={`Mean ${metrics.noise_mean ?? 'N/A'}, standard deviation ${metrics.noise_std ?? 'N/A'}.`} url={visualizations.noise_residual} />
        <ImagePanel title="Noise heatmap" description="Local residual variation after Gaussian denoising." url={visualizations.noise_heatmap} />
        <ImagePanel title="Canny edges" description={`Edge density ${metrics.edge_density ?? 'N/A'}.`} url={visualizations.edge_map} />
        <ImagePanel title="Sobel X" description="Measured horizontal gradient response." url={visualizations.sobel_x} />
        <ImagePanel title="Sobel Y" description="Measured vertical gradient response." url={visualizations.sobel_y} />
        <ImagePanel title="Laplacian" description={`Sharpness variance ${metrics.sharpness ?? 'N/A'}.`} url={visualizations.laplacian} />
      </div>
    </section>
  );
}
