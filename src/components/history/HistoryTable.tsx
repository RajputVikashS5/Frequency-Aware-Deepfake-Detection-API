import { Link } from 'react-router-dom';
import { Trash2, Search as SearchIcon, Filter, ArrowUpDown, History as HistoryIcon } from 'lucide-react';
import { useState, useMemo } from 'react';
import type { HistoryEntry, Verdict } from '@/types/analysis';
import { formatDate, verdictColor } from '@/utils/format';
import EmptyState from '@/components/common/EmptyState';
import VerdictBadge from '@/components/analysis/VerdictBadge';
import { config } from '@/config';

interface HistoryTableProps {
  entries: HistoryEntry[];
  onDelete: (id: string) => void;
  onClearAll: () => void;
}

type SortField = 'date' | 'verdict';
type SortDir = 'asc' | 'desc';

export default function HistoryTable({ entries, onDelete, onClearAll }: HistoryTableProps) {
  const [search, setSearch] = useState('');
  const [verdictFilter, setVerdictFilter] = useState<Verdict | 'all'>('all');
  const [sortField, setSortField] = useState<SortField>('date');
  const [sortDir, setSortDir] = useState<SortDir>('desc');
  const [page, setPage] = useState(0);

  const filtered = useMemo(() => {
    let result = entries;

    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter((e) => e.headline.toLowerCase().includes(q));
    }

    if (verdictFilter !== 'all') {
      result = result.filter((e) => e.verdict === verdictFilter);
    }

    result = [...result].sort((a, b) => {
      let cmp = 0;
      if (sortField === 'date') {
        cmp = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      } else {
        cmp = a.verdict.localeCompare(b.verdict);
      }
      return sortDir === 'desc' ? -cmp : cmp;
    });

    return result;
  }, [entries, search, verdictFilter, sortField, sortDir]);

  const pageSize = config.paginationPageSize;
  const totalPages = Math.ceil(filtered.length / pageSize);
  const pageItems = filtered.slice(page * pageSize, (page + 1) * pageSize);

  if (entries.length === 0) {
    return (
      <EmptyState
        icon={HistoryIcon}
        title="No analysis history yet"
        message="Your completed analyses will appear here. Run your first analysis to get started."
        action={
          <Link to="/analyze" className="btn-primary">
            <SearchIcon size={16} />
            Analyze News
          </Link>
        }
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-1 flex-col gap-2 sm:flex-row">
          <div className="relative flex-1">
            <SearchIcon size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(0);
              }}
              placeholder="Search by headline..."
              className="input-field py-2 pl-9 text-sm"
              aria-label="Search history by headline"
            />
          </div>
          <div className="relative">
            <Filter size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <select
              value={verdictFilter}
              onChange={(e) => {
                setVerdictFilter(e.target.value as Verdict | 'all');
                setPage(0);
              }}
              className="input-field py-2 pl-9 pr-8 text-sm"
              aria-label="Filter by verdict"
            >
              <option value="all">All verdicts</option>
              <option value="REAL">Real</option>
              <option value="FAKE">Fake</option>
              <option value="MISLEADING">Misleading</option>
              <option value="UNVERIFIED">Unverified</option>
            </select>
          </div>
          <button
            type="button"
            onClick={() => {
              setSortField((f) => (f === 'date' ? 'verdict' : 'date'));
              setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
            }}
            className="btn-secondary py-2 text-sm"
            aria-label={`Sort by ${sortField === 'date' ? 'verdict' : 'date'}, ${sortDir}`}
          >
            <ArrowUpDown size={14} />
            {sortField === 'date' ? 'Date' : 'Verdict'}
          </button>
        </div>
        <button
          type="button"
          onClick={onClearAll}
          className="inline-flex items-center justify-center gap-2 rounded-xl border border-red-500/20 bg-red-500/5 px-4 py-2 text-sm font-medium text-red-400 transition-colors hover:bg-red-500/10"
        >
          <Trash2 size={14} />
          Clear All
        </button>
      </div>

      <p className="text-xs text-slate-500">
        Showing {pageItems.length} of {filtered.length} {filtered.length === 1 ? 'entry' : 'entries'}
      </p>

      <div className="space-y-2">
        {pageItems.map((entry) => {
          const colors = verdictColor(entry.verdict);
          return (
            <div
              key={entry.analysis_id}
              className="glass-card-hover flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between"
            >
              <div className="flex items-center gap-3">
                <div className={`h-10 w-1.5 rounded-full bg-gradient-to-b ${colors.gradient}`} />
                <div className="min-w-0">
                  <Link
                    to={`/results/${entry.analysis_id}`}
                    className="block truncate text-sm font-medium text-slate-100 hover:text-cyan-400"
                  >
                    {entry.headline}
                  </Link>
                  <div className="mt-0.5 flex items-center gap-2 text-xs text-slate-500">
                    <span>{formatDate(entry.created_at)}</span>
                    <span>·</span>
                    <span>{entry.mode === 'text_image' ? 'Text + Image' : 'Text Only'}</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <VerdictBadge verdict={entry.verdict} size="sm" />
                <button
                  type="button"
                  onClick={() => onDelete(entry.analysis_id)}
                  className="rounded-lg p-2 text-slate-500 transition-colors hover:bg-red-500/10 hover:text-red-400"
                  aria-label={`Delete analysis "${entry.headline}"`}
                >
                  <Trash2 size={15} />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 pt-4">
          <button
            type="button"
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0}
            className="btn-secondary px-3 py-1.5 text-sm disabled:opacity-30"
          >
            Previous
          </button>
          <span className="text-xs text-slate-500">
            Page {page + 1} of {totalPages}
          </span>
          <button
            type="button"
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            disabled={page >= totalPages - 1}
            className="btn-secondary px-3 py-1.5 text-sm disabled:opacity-30"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
