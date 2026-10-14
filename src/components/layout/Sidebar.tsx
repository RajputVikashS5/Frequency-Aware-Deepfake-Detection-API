import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Search,
  History,
  Info,
  Mail,
  ShieldCheck,
  X,
} from 'lucide-react';

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/analyze', label: 'Analyze News', icon: Search, end: false },
  { to: '/history', label: 'History', icon: History, end: false },
  { to: '/about', label: 'About & Method', icon: Info, end: false },
  { to: '/contact', label: 'Contact', icon: Mail, end: false },
];

export default function Sidebar({ open, onClose }: SidebarProps) {
  return (
    <>
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      <aside
        className={`fixed left-0 top-0 z-50 flex h-screen w-64 flex-col border-r border-slate-200 bg-white/95 backdrop-blur-xl transition-transform duration-300 dark:border-white/10 dark:bg-slate-950/95 lg:translate-x-0 ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
        aria-label="Primary navigation"
      >
        <div className="flex items-center justify-between px-5 py-5">
          <NavLink to="/" className="flex items-center gap-2.5" onClick={onClose}>
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 shadow-lg shadow-cyan-500/20">
              <ShieldCheck size={20} className="text-white" />
            </div>
            <div>
              <span className="block text-sm font-bold text-slate-100">TruthLens AI</span>
              <span className="block text-[10px] text-slate-500">Fake News Detection</span>
            </div>
          </NavLink>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-white/5 hover:text-slate-200 lg:hidden"
            aria-label="Close sidebar"
          >
            <X size={18} />
          </button>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-2 scrollbar-thin">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              onClick={onClose}
              className={({ isActive }) =>
                `sidebar-link ${isActive ? 'sidebar-link-active' : ''}`
              }
            >
              <item.icon size={18} />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-white/5 px-5 py-4">
          <p className="text-[10px] leading-relaxed text-slate-600">
            Automated predictions are not definitive proof. Always verify with primary sources.
          </p>
        </div>
      </aside>
    </>
  );
}
