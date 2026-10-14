import { useState } from 'react';
import { History as HistoryIcon } from 'lucide-react';
import PageHeader from '@/components/common/PageHeader';
import HistoryTable from '@/components/history/HistoryTable';
import ConfirmationDialog from '@/components/common/ConfirmationDialog';
import { useHistory } from '@/hooks/useHistory';
import { useToast } from '@/hooks/useToast';

export default function HistoryPage() {
  const { history, removeEntry, clearAll } = useHistory();
  const { addToast } = useToast();
  const [confirmOpen, setConfirmOpen] = useState(false);

  const handleDelete = (id: string) => {
    removeEntry(id);
    addToast('Entry deleted.', 'info');
  };

  const handleClearAll = () => {
    clearAll();
    setConfirmOpen(false);
    addToast('History cleared.', 'info');
  };

  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader
        title="Analysis History"
        subtitle="Your past analyses, stored locally in this browser."
        icon={<HistoryIcon size={20} />}
      />

      <div className="mb-4 flex items-start gap-3 rounded-xl border border-white/10 bg-white/5 p-3">
        <HistoryIcon size={14} className="mt-0.5 flex-shrink-0 text-slate-500" />
        <p className="text-xs leading-relaxed text-slate-400">
          History is stored only in this browser's local storage. It is not shared across devices
          or other users. Uploaded images and full article contents are not stored. Clearing your
          browser data will remove this history.
        </p>
      </div>

      <HistoryTable
        entries={history}
        onDelete={handleDelete}
        onClearAll={() => setConfirmOpen(true)}
      />

      <ConfirmationDialog
        open={confirmOpen}
        title="Clear all history?"
        message="This will permanently delete all analysis history from this browser. This action cannot be undone."
        confirmLabel="Clear All"
        onConfirm={handleClearAll}
        onCancel={() => setConfirmOpen(false)}
      />
    </div>
  );
}
