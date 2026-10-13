import React, { useEffect } from 'react';
import { X, CheckCircle, RefreshCw } from 'lucide-react';
import { formatBytes } from '../../utils/formatters';
import { safeRevokeUrl } from '../../utils/fileValidation';

export default function ImagePreview({ file, previewUrl, dimensions, onRemove, onReplace }) {
  useEffect(() => {
    // Cleanup Object URL on unmount
    return () => {
      safeRevokeUrl(previewUrl);
    };
  }, [previewUrl]);

  if (!file || !previewUrl) return null;

  return (
    <div className="bg-card rounded-xl border border-border p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
      <div className="flex items-center space-x-4 w-full sm:w-auto">
        <div className="relative w-16 h-16 sm:w-20 sm:h-20 rounded-lg overflow-hidden border border-border shrink-0 bg-canvas">
          <img
            src={previewUrl}
            alt={file.name}
            className="w-full h-full object-cover"
          />
        </div>
        <div className="space-y-1 min-w-0">
          <div className="flex items-center space-x-2">
            <h4 className="text-sm font-semibold text-slate-100 truncate max-w-xs sm:max-w-md">
              {file.name}
            </h4>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-950/40 text-emerald-400 border border-emerald-900/60 shrink-0">
              Validated
            </span>
          </div>
          <div className="flex flex-wrap gap-x-3 text-xs text-slate-400 font-mono">
            <span>{formatBytes(file.size)}</span>
            {dimensions && (
              <span>{dimensions.width} × {dimensions.height} px</span>
            )}
            <span className="uppercase">{file.type.split('/')[1] || 'IMG'}</span>
          </div>
        </div>
      </div>

      <div className="flex items-center space-x-2 w-full sm:w-auto justify-end pt-2 sm:pt-0 border-t sm:border-t-0 border-border">
        {onReplace && (
          <button
            type="button"
            onClick={onReplace}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-slate-100 bg-card-subtle hover:bg-card-hover rounded-md border border-border transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5 text-slate-400" />
            <span>Replace</span>
          </button>
        )}
        {onRemove && (
          <button
            type="button"
            onClick={onRemove}
            className="inline-flex items-center space-x-1 px-3 py-1.5 text-xs font-medium text-red-400 hover:text-red-300 hover:bg-red-950/20 rounded-md border border-red-950/50 transition-colors"
          >
            <X className="w-3.5 h-3.5" />
            <span>Remove</span>
          </button>
        )}
      </div>
    </div>
  );
}
