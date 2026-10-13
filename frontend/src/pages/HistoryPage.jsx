import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import PageLayout from '../components/layout/PageLayout';
import HistoryTable from '../components/history/HistoryTable';
import HistoryFilters from '../components/history/HistoryFilters';
import EmptyState from '../components/common/EmptyState';
import ConfirmDialog from '../components/common/ConfirmDialog';
import { historyService } from '../services/historyService';
import { History, Info } from 'lucide-react';

export default function HistoryPage() {
  const navigate = useNavigate();

  const [records, setRecords] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [showConfirmClear, setShowConfirmClear] = useState(false);

  // Load history records on mount
  useEffect(() => {
    loadData();
  }, []);

  const loadData = () => {
    const list = historyService.searchAndFilter(searchQuery, filterType);
    setRecords(list);
  };

  useEffect(() => {
    loadData();
  }, [searchQuery, filterType]);

  const handleDeleteItem = (id) => {
    historyService.deleteAnalysis(id);
    loadData();
  };

  const handleConfirmClearAll = () => {
    historyService.clearAllHistory();
    setShowConfirmClear(false);
    loadData();
  };

  return (
    <PageLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="border-b border-border pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-100 tracking-tight flex items-center space-x-2">
              <History className="w-6 h-6 text-accent-cyan" />
              <span>Inspection History</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">
              Review past forensic inspections stored within your current browser session.
            </p>
          </div>
        </div>

        {/* Local Storage Disclaimer Box */}
        <div className="bg-card-subtle p-3.5 rounded-xl border border-border flex items-start space-x-2.5 text-xs text-slate-400">
          <Info className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            History records are saved in your browser's local sandbox (<code className="text-slate-300">localStorage</code>). Records are not synchronized across devices. Clearing your browser cache will erase this log.
          </p>
        </div>

        {/* Filters & Search */}
        <HistoryFilters
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          activeFilter={filterType}
          onFilterChange={setFilterType}
          onClearHistory={records.length > 0 ? () => setShowConfirmClear(true) : null}
        />

        {/* Records Table or Empty State */}
        {records.length > 0 ? (
          <HistoryTable
            records={records}
            onDeleteItem={handleDeleteItem}
          />
        ) : (
          <EmptyState
            title={searchQuery || filterType !== 'all' ? 'No matching records' : 'No history yet'}
            description={
              searchQuery || filterType !== 'all'
                ? 'Try adjusting your search query or verdict filter.'
                : 'Upload an image on the Analyze page to view your first forensic inspection log.'
            }
            actionText="Run New Analysis"
            onAction={() => navigate('/analyze')}
          />
        )}

        {/* Confirmation Dialog for Clearing History */}
        <ConfirmDialog
          isOpen={showConfirmClear}
          title="Clear Entire Inspection History?"
          message="This action will delete all local analysis records from this browser. This cannot be undone."
          confirmLabel="Delete All Records"
          isDestructive={true}
          onConfirm={handleConfirmClearAll}
          onCancel={() => setShowConfirmClear(false)}
        />
      </div>
    </PageLayout>
  );
}
