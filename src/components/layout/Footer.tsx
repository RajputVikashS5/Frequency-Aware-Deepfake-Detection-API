import { ShieldCheck } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="border-t border-white/10 px-6 py-5">
      <div className="flex flex-col items-center justify-between gap-3 text-center sm:flex-row sm:text-left">
        <div className="flex items-center gap-2">
          <ShieldCheck size={16} className="text-cyan-400" />
          <span className="text-xs text-slate-500">
            TruthLens AI — Final-Year AIML Major Project
          </span>
        </div>
        <p className="text-xs text-slate-600">
          Automated predictions are not definitive proof. Verify with primary sources.
        </p>
      </div>
    </footer>
  );
}
