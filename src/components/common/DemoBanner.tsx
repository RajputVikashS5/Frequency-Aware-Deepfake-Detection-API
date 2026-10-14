import { AlertTriangle } from 'lucide-react';
import { config } from '@/config';

export default function DemoBanner() {
  if (!config.demoMode) return null;

  return (
    <div className="flex items-center justify-center gap-2 bg-amber-500/10 px-4 py-2 text-center">
      <AlertTriangle size={14} className="text-amber-400" />
      <p className="text-xs font-medium text-amber-400">
        Demo Mode — Sample Data. Predictions shown are not real AI analysis.
      </p>
    </div>
  );
}
