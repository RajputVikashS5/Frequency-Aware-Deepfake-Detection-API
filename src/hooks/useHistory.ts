import { useCallback, useEffect, useState } from 'react';
import { getHistory, saveHistoryEntry, deleteHistoryEntry, clearHistory } from '@/utils/history';
import type { HistoryEntry } from '@/types/analysis';

export function useHistory() {
  const [history, setHistory] = useState<HistoryEntry[]>([]);

  useEffect(() => {
    setHistory(getHistory());
  }, []);

  const addEntry = useCallback((entry: HistoryEntry) => {
    setHistory(saveHistoryEntry(entry));
  }, []);

  const removeEntry = useCallback((id: string) => {
    setHistory(deleteHistoryEntry(id));
  }, []);

  const clearAll = useCallback(() => {
    clearHistory();
    setHistory([]);
  }, []);

  return { history, addEntry, removeEntry, clearAll };
}
