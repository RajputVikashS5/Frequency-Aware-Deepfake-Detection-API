import { BookOpen } from 'lucide-react';
import type { EvidenceItem } from '@/types/analysis';
import EvidenceItemCard from '@/components/evidence/EvidenceItem';

export default function EvidenceList({ items }: { items: EvidenceItem[] }) {
  if (!items || items.length === 0) {
    return (
      <div className="glass-card p-5">
        <div className="mb-4 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-500/10">
            <BookOpen size={18} className="text-cyan-400" />
          </div>
          <h3 className="text-base font-semibold text-slate-100">Evidence</h3>
        </div>
        <p className="text-sm text-slate-500">
          No evidence sources were retrieved for this analysis.
        </p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-3 flex items-center gap-2">
        <BookOpen size={16} className="text-cyan-400" />
        <h3 className="text-base font-semibold text-slate-100">
          Retrieved Evidence
        </h3>
        <span className="text-xs text-slate-500">({items.length} source{items.length !== 1 ? 's' : ''})</span>
      </div>
      <div className="space-y-3">
        {items.map((item, i) => (
          <EvidenceItemCard key={i} item={item} />
        ))}
      </div>
    </div>
  );
}
