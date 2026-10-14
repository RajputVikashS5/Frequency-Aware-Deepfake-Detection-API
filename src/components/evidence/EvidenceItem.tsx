import { ExternalLink, ThumbsUp, ThumbsDown, MinusCircle, Newspaper } from 'lucide-react';
import type { EvidenceItem, EvidenceClassification } from '@/types/analysis';

const classConfig: Record<
  EvidenceClassification,
  { icon: typeof ThumbsUp; color: string; label: string }
> = {
  supports: { icon: ThumbsUp, color: 'text-emerald-400 bg-emerald-500/10', label: 'Supports' },
  contradicts: { icon: ThumbsDown, color: 'text-red-400 bg-red-500/10', label: 'Contradicts' },
  insufficient: { icon: MinusCircle, color: 'text-slate-400 bg-slate-500/10', label: 'Insufficient' },
};

export default function EvidenceItemCard({ item }: { item: EvidenceItem }) {
  const cls = item.classification ? classConfig[item.classification] : null;
  const ClassIcon = cls?.icon;

  return (
    <div className="glass-card-hover p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-white/5">
            <Newspaper size={16} className="text-slate-400" />
          </div>
          <div className="min-w-0">
            <h4 className="text-sm font-semibold text-slate-100">{item.source_title}</h4>
            {item.publisher && (
              <p className="mt-0.5 text-xs text-slate-500">{item.publisher}</p>
            )}
          </div>
        </div>
        {cls && ClassIcon && (
          <span
            className={`inline-flex flex-shrink-0 items-center gap-1 rounded-full px-2.5 py-1 text-[10px] font-medium ${cls.color}`}
          >
            <ClassIcon size={11} />
            {cls.label}
          </span>
        )}
      </div>

      <p className="mt-3 text-sm leading-relaxed text-slate-400">{item.excerpt}</p>

      {item.url && (
        <a
          href={item.url}
          target="_blank"
          rel="noopener noreferrer nofollow"
          className="mt-3 inline-flex items-center gap-1.5 text-xs font-medium text-cyan-400 transition-colors hover:text-cyan-300"
        >
          <ExternalLink size={12} />
          View original source
        </a>
      )}
    </div>
  );
}
