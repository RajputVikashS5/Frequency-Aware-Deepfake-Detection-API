import type { AnalysisResponse } from '@/types/analysis';

const resultsKey = 'truthlens_results';

export function saveResult(result: AnalysisResponse): void {
  try {
    const raw = localStorage.getItem(resultsKey);
    const map: Record<string, AnalysisResponse> = raw ? JSON.parse(raw) : {};
    map[result.analysis_id] = result;
    const keys = Object.keys(map);
    if (keys.length > 50) {
      const sorted = keys.sort(
        (a, b) =>
          new Date(map[a].created_at).getTime() - new Date(map[b].created_at).getTime()
      );
      for (const k of sorted.slice(0, keys.length - 50)) {
        delete map[k];
      }
    }
    localStorage.setItem(resultsKey, JSON.stringify(map));
  } catch {
    // ignore storage errors
  }
}

export function getResult(id: string): AnalysisResponse | null {
  try {
    const raw = localStorage.getItem(resultsKey);
    if (!raw) return null;
    const map: Record<string, AnalysisResponse> = JSON.parse(raw);
    return map[id] ?? null;
  } catch {
    return null;
  }
}
