import { Menu, ShieldCheck } from 'lucide-react';
import ThemeToggle from '@/components/layout/ThemeToggle';
import { config } from '@/config';

interface TopbarProps {
  onMenuClick: () => void;
}

export default function Topbar({ onMenuClick }: TopbarProps) {
  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-200 bg-white/80 px-4 backdrop-blur-xl dark:border-white/10 dark:bg-slate-950/80 lg:px-6">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onMenuClick}
          className="rounded-lg p-2 text-slate-500 hover:bg-slate-200/60 hover:text-slate-700 dark:text-slate-400 dark:hover:bg-white/5 dark:hover:text-slate-200 lg:hidden"
          aria-label="Open sidebar"
        >
          <Menu size={20} />
        </button>
        <div className="flex items-center gap-2 lg:hidden">
          <ShieldCheck size={20} className="text-cyan-400" />
          <span className="text-sm font-bold text-slate-800 dark:text-slate-100">TruthLens AI</span>
        </div>
        <div className="hidden lg:block">
          <h2 className="text-sm font-medium text-slate-500 dark:text-slate-400">
            Multimodal Fake News Detection
          </h2>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {config.demoMode && (
          <span className="hidden items-center gap-1.5 rounded-full bg-amber-500/10 px-3 py-1 text-xs font-medium text-amber-400 sm:inline-flex">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
            Demo Mode
          </span>
        )}
        <ThemeToggle />
      </div>
    </header>
  );
}
