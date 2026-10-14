import { config } from '@/config';
import { analyzeNews } from '@/services/api';
import { createDemoResponse } from '@/data/demoData';
import type { AnalysisRequest, AnalysisResponse } from '@/types/analysis';

function delay(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}

export async function submitAnalysis(
  req: AnalysisRequest
): Promise<AnalysisResponse> {
  if (config.demoMode || !config.apiBaseUrl) {
    await delay(2200);
    return createDemoResponse(
      req.headline,
      req.article_text,
      req.source_url,
      req.mode,
      !!req.image
    );
  }

  return analyzeNews({
    headline: req.headline,
    article_text: req.article_text,
    source_url: req.source_url,
    mode: req.mode,
    image: req.image,
  });
}
