import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export default function ErrorState({
  title = 'Something went wrong',
  message,
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-red-500/20 bg-red-500/5 px-6 py-10 text-center">
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-red-500/10">
        <AlertCircle size={24} className="text-red-400" />
      </div>
      <h3 className="mb-1.5 text-base font-semibold text-slate-100">{title}</h3>
      <p className="mb-4 max-w-md text-sm text-slate-400">{message}</p>
      {onRetry && (
        <button type="button" onClick={onRetry} className="btn-primary">
          <RefreshCw size={16} />
          Try Again
        </button>
      )}
    </div>
  );
}
