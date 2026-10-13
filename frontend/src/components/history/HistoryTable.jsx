import React from 'react';
import { Link } from 'react-router-dom';
import { Trash2, ExternalLink, Image as ImageIcon } from 'lucide-react';
import PredictionBadge from '../common/PredictionBadge';
import { formatDate, formatBytes } from '../../utils/formatters';

export default function HistoryTable({ records, onDeleteItem }) {
  if (!records || records.length === 0) return null;

  return (
    <div className="bg-card rounded-xl border border-border shadow-sm overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-card-subtle border-b border-border text-slate-400 uppercase font-mono text-[10px] tracking-wider">
            <tr>
              <th className="py-3 px-4">Sample Preview</th>
              <th className="py-3 px-4">Filename & Size</th>
              <th className="py-3 px-4">Analysis Date</th>
              <th className="py-3 px-4">Verdict</th>
              <th className="py-3 px-4 font-mono">Confidence</th>
              <th className="py-3 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {records.map((item) => (
              <tr key={item.id} className="hover:bg-card-hover/40 transition-colors">
                {/* Thumbnail */}
                <td className="py-3 px-4">
                  <div className="w-10 h-10 rounded bg-canvas border border-border overflow-hidden flex items-center justify-center">
                    {item.originalPreviewUrl ? (
                      <img
                        src={item.originalPreviewUrl}
                        alt={item.filename}
                        className="w-full h-full object-cover"
                      />
                    ) : item.fftSpectrumUrl ? (
                      <img
                        src={item.fftSpectrumUrl}
                        alt="FFT"
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <ImageIcon className="w-4 h-4 text-slate-500" />
                    )}
                  </div>
                </td>

                {/* Filename & size */}
                <td className="py-3 px-4">
                  <span className="font-semibold text-slate-200 block truncate max-w-xs">
                    {item.filename}
                  </span>
                  <span className="text-[11px] text-slate-500 font-mono">
                    {formatBytes(item.fileSize)}
                  </span>
                </td>

                {/* Date */}
                <td className="py-3 px-4 text-slate-400 whitespace-nowrap">
                  {formatDate(item.timestamp)}
                </td>

                {/* Verdict */}
                <td className="py-3 px-4">
                  <PredictionBadge isManipulated={item.isManipulated} />
                </td>

                {/* Confidence */}
                <td className="py-3 px-4 font-mono font-bold text-slate-200">
                  {Number(item.confidencePct || 0).toFixed(1)}%
                </td>

                {/* Actions */}
                <td className="py-3 px-4 text-right space-x-2 whitespace-nowrap">
                  <Link
                    to={`/results/${item.id}`}
                    className="inline-flex items-center space-x-1 px-2.5 py-1 text-xs font-medium text-accent-cyan bg-card-subtle hover:bg-card-hover border border-border rounded transition-colors"
                  >
                    <span>View</span>
                    <ExternalLink className="w-3 h-3" />
                  </Link>

                  {onDeleteItem && (
                    <button
                      type="button"
                      onClick={() => onDeleteItem(item.id)}
                      className="p-1 text-slate-400 hover:text-red-400 transition-colors"
                      title="Delete record"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
