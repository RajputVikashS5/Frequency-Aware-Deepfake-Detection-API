import { CheckCircle, XCircle, Info, AlertTriangle, X } from 'lucide-react';
import { useToast } from '@/hooks/useToast';
import { useReducedMotion } from '@/hooks/useReducedMotion';
import type { Toast as ToastType } from '@/hooks/useToast';

const iconMap = {
  success: CheckCircle,
  error: XCircle,
  info: Info,
  warning: AlertTriangle,
};

const colorMap = {
  success: 'border-emerald-500/30 text-emerald-400',
  error: 'border-red-500/30 text-red-400',
  info: 'border-cyan-500/30 text-cyan-400',
  warning: 'border-amber-500/30 text-amber-400',
};

export default function ToastContainer() {
  const { toasts, removeToast } = useToast();
  const reduced = useReducedMotion();

  return (
    <div
      className="fixed bottom-4 right-4 z-[70] flex flex-col gap-2 sm:bottom-6 sm:right-6"
      aria-live="polite"
      aria-atomic="true"
    >
      {toasts.map((toast: ToastType) => {
        const Icon = iconMap[toast.type];
        return (
          <div
            key={toast.id}
            className={`flex items-center gap-3 rounded-xl border bg-slate-900/95 px-4 py-3 shadow-xl backdrop-blur-md ${
              colorMap[toast.type]
            } ${reduced ? '' : 'animate-[slideIn_0.2s_ease-out]'}`}
            role="status"
          >
            <Icon size={16} className="flex-shrink-0" />
            <p className="flex-1 text-sm text-slate-200">{toast.message}</p>
            <button
              type="button"
              onClick={() => removeToast(toast.id)}
              className="text-slate-500 hover:text-slate-300"
              aria-label="Dismiss notification"
            >
              <X size={14} />
            </button>
          </div>
        );
      })}
    </div>
  );
}
