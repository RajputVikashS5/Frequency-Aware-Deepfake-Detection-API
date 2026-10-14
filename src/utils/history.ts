import { config } from '@/config';
import type { HistoryEntry } from '@/types/analysis';

export function getHistory(): HistoryEntry[] {
  try {
    const raw = localStorage.getItem(config.historyStorageKey);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed as HistoryEntry[];
  } catch {
    return [];
  }
}

export function saveHistoryEntry(entry: HistoryEntry): HistoryEntry[] {
  const current = getHistory();
  const updated = [entry, ...current].slice(0, 100);
  try {
    localStorage.setItem(config.historyStorageKey, JSON.stringify(updated));
  } catch {
    // storage may be full or unavailable; silently ignore
  }
  return updated;
}

export function deleteHistoryEntry(id: string): HistoryEntry[] {
  const current = getHistory();
  const updated = current.filter((e) => e.analysis_id !== id);
  try {
    localStorage.setItem(config.historyStorageKey, JSON.stringify(updated));
  } catch {
    // ignore
  }
  return updated;
}

export function clearHistory(): void {
  try {
    localStorage.removeItem(config.historyStorageKey);
  } catch {
    // ignore
  }
}
