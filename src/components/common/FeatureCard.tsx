import type { LucideIcon } from 'lucide-react';
import type { ReactNode } from 'react';

interface FeatureCardProps {
  icon: LucideIcon;
  title: string;
  description: string;
  accent?: string;
  children?: ReactNode;
}

export default function FeatureCard({
  icon: Icon,
  title,
  description,
  accent = 'from-cyan-500 to-blue-600',
  children,
}: FeatureCardProps) {
  return (
    <div className="glass-card-hover group p-5">
      <div
        className={`mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br ${accent} shadow-lg transition-transform duration-300 group-hover:scale-110`}
      >
        <Icon size={20} className="text-white" />
      </div>
      <h3 className="mb-2 text-base font-semibold text-slate-100">{title}</h3>
      <p className="text-sm leading-relaxed text-slate-400">{description}</p>
      {children}
    </div>
  );
}
