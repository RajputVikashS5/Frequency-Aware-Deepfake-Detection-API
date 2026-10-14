import type { LucideIcon } from 'lucide-react';

interface StatCardProps {
  icon: LucideIcon;
  label: string;
  value: string | number;
  accent?: string;
}

export default function StatCard({
  icon: Icon,
  label,
  value,
  accent = 'text-cyan-400',
}: StatCardProps) {
  return (
    <div className="glass-card p-4">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/5">
          <Icon size={18} className={accent} />
        </div>
        <div>
          <p className="text-xs text-slate-500">{label}</p>
          <p className="text-lg font-bold text-slate-100">{value}</p>
        </div>
      </div>
    </div>
  );
}
