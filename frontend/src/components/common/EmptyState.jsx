import React from 'react';
import { Inbox } from 'lucide-react';

export default function EmptyState({
  title = 'No items found',
  description = 'There are no records matching your criteria.',
  icon: Icon = Inbox,
  actionText,
  onAction,
}) {
  return (
    <div className="bg-card rounded-xl border border-border p-12 text-center flex flex-col items-center justify-center space-y-3">
      <div className="p-3 bg-card-subtle rounded-xl text-slate-400 border border-border">
        <Icon className="w-8 h-8 text-slate-400" />
      </div>
      <h3 className="font-bold text-slate-200 text-sm">{title}</h3>
      <p className="text-xs text-slate-400 max-w-sm leading-relaxed">{description}</p>
      {actionText && onAction && (
        <button
          type="button"
          onClick={onAction}
          className="mt-2 px-4 py-2 text-xs font-semibold text-canvas bg-accent-cyan hover:bg-accent-cyan-light rounded-md transition-colors"
        >
          {actionText}
        </button>
      )}
    </div>
  );
}
