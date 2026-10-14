import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Info } from 'lucide-react';
import PageHeader from '@/components/common/PageHeader';
import NewsInputForm, { type NewsFormValues } from '@/components/analysis/NewsInputForm';
import AnalysisProgress from '@/components/analysis/AnalysisProgress';
import ErrorState from '@/components/common/ErrorState';
import { submitAnalysis } from '@/services/analysisService';
import { useHistory } from '@/hooks/useHistory';
import { useToast } from '@/hooks/useToast';
import { saveResult } from '@/utils/resultsStore';
import type { AnalysisResponse, ApiError } from '@/types/analysis';

export default function AnalyzePage() {
  const navigate = useNavigate();
  const { addEntry } = useHistory();
  const { addToast } = useToast();

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progressMode, setProgressMode] = useState<'text_image' | 'text_only'>('text_image');

  const handleSubmit = async (values: NewsFormValues) => {
    setIsSubmitting(true);
    setError(null);
    setProgressMode(values.mode);

    try {
      const result: AnalysisResponse = await submitAnalysis({
        headline: values.headline,
        article_text: values.article_text,
        source_url: values.source_url,
        mode: values.mode,
        image: values.image ?? undefined,
      });



      addEntry({
        analysis_id: result.analysis_id,
        headline: result.headline,
        verdict: result.verdict,
        confidence: result.confidence,
        mode: result.mode,
        created_at: result.created_at,
        has_image: values.mode === 'text_image' && !!values.image,
      });

      saveResult(result);

      addToast('Analysis complete.', 'success');
      navigate(`/results/${result.analysis_id}`);
    } catch (e) {
      const apiError = e as ApiError;
      setError(apiError.message || 'An unexpected error occurred during analysis.');
      addToast('Analysis failed.', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader
        title="Analyze News"
        subtitle="Submit a news headline, article text, and an optional image for verification."
        icon={<Search size={20} />}
      />

      {isSubmitting ? (
        <AnalysisProgress mode={progressMode} />
      ) : error ? (
        <ErrorState
          message={error}
          onRetry={() => setError(null)}
        />
      ) : (
        <>
          <div className="mb-4 flex items-start gap-3 rounded-xl border border-cyan-500/20 bg-cyan-500/5 p-3">
            <Info size={16} className="mt-0.5 flex-shrink-0 text-cyan-400" />
            <p className="text-xs leading-relaxed text-slate-400">
              Choose Text + Image mode for full multimodal analysis, or Text Only mode if you don't
              have an image. All fields marked with <span className="text-red-400">*</span> are required.
            </p>
          </div>
          <div className="glass-card p-5 sm:p-6">
            <NewsInputForm onSubmit={handleSubmit} isSubmitting={isSubmitting} />
          </div>
        </>
      )}
    </div>
  );
}
