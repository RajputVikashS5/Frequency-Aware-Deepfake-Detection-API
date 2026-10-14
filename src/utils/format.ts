import type { Verdict } from '@/types/analysis';

export function formatDate(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return iso;
  }
}

export function verdictColor(verdict: Verdict): {
  text: string;
  bg: string;
  border: string;
  gradient: string;
} {
  switch (verdict) {
    case 'REAL':
      return {
        text: 'text-emerald-400',
        bg: 'bg-emerald-500/10',
        border: 'border-emerald-500/30',
        gradient: 'from-emerald-500 to-teal-500',
      };
    case 'FAKE':
      return {
        text: 'text-red-400',
        bg: 'bg-red-500/10',
        border: 'border-red-500/30',
        gradient: 'from-red-500 to-rose-500',
      };
    case 'MISLEADING':
      return {
        text: 'text-amber-400',
        bg: 'bg-amber-500/10',
        border: 'border-amber-500/30',
        gradient: 'from-amber-500 to-orange-500',
      };
    default:
      return {
        text: 'text-sky-400',
        bg: 'bg-sky-500/10',
        border: 'border-sky-500/30',
        gradient: 'from-sky-500 to-blue-500',
      };
  }
}
