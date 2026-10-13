import React from 'react';
import { formatBytes } from '../../utils/formatters';

export default function FileMetadata({ metadata }) {
  if (!metadata) return null;

  return (
    <div className="bg-card rounded-xl border border-border p-4 text-xs font-mono">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div>
          <span className="text-slate-500 block text-[10px] uppercase">File Name</span>
          <span className="text-slate-200 truncate block mt-0.5" title={metadata.filename}>
            {metadata.filename || '—'}
          </span>
        </div>
        <div>
          <span className="text-slate-500 block text-[10px] uppercase">Dimensions</span>
          <span className="text-slate-200 block mt-0.5">
            {metadata.dimensions || (metadata.width && metadata.height ? `${metadata.width} × ${metadata.height} px` : '256 × 256 px')}
          </span>
        </div>
        <div>
          <span className="text-slate-500 block text-[10px] uppercase">File Size</span>
          <span className="text-slate-200 block mt-0.5">
            {formatBytes(metadata.fileSize || metadata.size)}
          </span>
        </div>
        <div>
          <span className="text-slate-500 block text-[10px] uppercase">Integrity Check</span>
          <span className="text-slate-200 truncate block mt-0.5 font-mono text-[11px]" title={metadata.sha256Digest}>
            {metadata.sha256Digest ? `${metadata.sha256Digest.slice(0, 10)}...` : 'SHA-256 (Calculated)'}
          </span>
        </div>
      </div>
    </div>
  );
}
