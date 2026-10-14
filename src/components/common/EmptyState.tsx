import type { LucideIcon } from 'lucide-react';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  message: string;
  action?: React.ReactNode;
}

export default function EmptyState({ icon: Icon, title, message, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-white/10 bg-white/[0.02] px-6 py-12 text-center">
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-white/5">
        <Icon size={24} className="text-slate-500" />
      </div>
      <h3 className="mb-1.5 text-base font-semibold text-slate-200">{title}</h3>
      <p className="mb-4 max-w-md text-sm text-slate-500">{message}</p>
      {action}
    </div>
  );
}
