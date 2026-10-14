import { Moon, Sun } from 'lucide-react';
import { useTheme } from '@/hooks/useTheme';
import { useReducedMotion } from '@/hooks/useReducedMotion';

export default function ThemeToggle() {
  const { theme, toggle } = useTheme();
  const reduced = useReducedMotion();

  return (
    <button
      type="button"
      onClick={toggle}
      className="relative flex h-9 w-9 items-center justify-center rounded-lg border border-slate-300 bg-white text-slate-600 transition-colors hover:border-slate-400 dark:border-white/10 dark:bg-white/5 dark:text-slate-300 dark:hover:border-white/20 dark:hover:text-slate-100"
      aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
      title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
    >
      {theme === 'dark' ? (
        <Sun size={18} className={!reduced ? 'transition-transform duration-300' : ''} />
      ) : (
        <Moon size={18} className={!reduced ? 'transition-transform duration-300' : ''} />
      )}
    </button>
  );
}
