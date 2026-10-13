import React from 'react';
import { Search, Filter } from 'lucide-react';

export default function HistoryFilters({ searchQuery, onSearchChange, activeFilter, onFilterChange, onClearHistory }) {
  return (
    <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 bg-card p-4 rounded-xl border border-border">
      {/* Search Input */}
      <div className="relative flex-1 max-w-md">
        <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Search by file name..."
          className="w-full bg-canvas border border-border rounded-lg pl-9 pr-4 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-accent-cyan"
        />
      </div>

      {/* Filter Tabs & Clear Action */}
      <div className="flex items-center space-x-2">
        <div className="flex bg-canvas p-1 rounded-lg border border-border text-xs">
          <button
            type="button"
            onClick={() => onFilterChange('all')}
            className={`px-3 py-1 rounded font-medium transition-colors ${
              activeFilter === 'all'
                ? 'bg-card-subtle text-accent-cyan font-semibold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            All
          </button>
          <button
            type="button"
            onClick={() => onFilterChange('real')}
            className={`px-3 py-1 rounded font-medium transition-colors ${
              activeFilter === 'real'
                ? 'bg-card-subtle text-emerald-400 font-semibold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Likely Real
          </button>
          <button
            type="button"
            onClick={() => onFilterChange('manipulated')}
            className={`px-3 py-1 rounded font-medium transition-colors ${
              activeFilter === 'manipulated'
                ? 'bg-card-subtle text-red-400 font-semibold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Manipulated
          </button>
        </div>

        {onClearHistory && (
          <button
            type="button"
            onClick={onClearHistory}
            className="px-3 py-2 text-xs font-medium text-red-400 hover:text-red-300 hover:bg-red-950/20 border border-red-950/50 rounded-lg transition-colors whitespace-nowrap"
          >
            Clear History
          </button>
        )}
      </div>
    </div>
  );
}
