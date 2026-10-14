import { CheckCircle, XCircle, AlertTriangle, HelpCircle } from 'lucide-react';
import type { Verdict } from '@/types/analysis';
import { verdictColor } from '@/utils/format';

interface VerdictBadgeProps {
  verdict: Verdict;
  size?: 'sm' | 'md' | 'lg';
}

const iconMap = {
  REAL: CheckCircle,
  FAKE: XCircle,
  MISLEADING: AlertTriangle,
  UNVERIFIED: HelpCircle,
};

const labelMap = {
  REAL: 'Real',
  FAKE: 'Fake',
  MISLEADING: 'Misleading',
  UNVERIFIED: 'Unverified',
};

export default function VerdictBadge({ verdict, size = 'md' }: VerdictBadgeProps) {
  const colors = verdictColor(verdict);
  const Icon = iconMap[verdict];

  const sizeClasses = {
    sm: 'px-3 py-1 text-xs gap-1.5',
    md: 'px-4 py-2 text-sm gap-2',
    lg: 'px-6 py-3 text-base gap-2.5',
  };

  const iconSizes = {
    sm: 14,
    md: 18,
    lg: 22,
  };

  return (
    <span
      className={`inline-flex items-center rounded-full border font-semibold ${colors.bg} ${colors.border} ${colors.text} ${sizeClasses[size]}`}
    >
      <Icon size={iconSizes[size]} />
      {labelMap[verdict]}
    </span>
  );
}
