import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Copy,
  Printer,
  ExternalLink,
  Search,
  Clock,
  Hash,
  FileText,
  Image as ImageIcon,
  AlertTriangle,
} from 'lucide-react';
import PageHeader from '@/components/common/PageHeader';
import VerdictBadge from '@/components/analysis/VerdictBadge';
import ConfidenceIndicator from '@/components/analysis/ConfidenceIndicator';
import TextAnalysisCard from '@/components/analysis/TextAnalysisCard';
import ImageAnalysisCard from '@/components/analysis/ImageAnalysisCard';
import EvidenceList from '@/components/evidence/EvidenceList';
import ExplanationPanel from '@/components/analysis/ExplanationPanel';
import ErrorState from '@/components/common/ErrorState';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import { getResult } from '@/utils/resultsStore';
import { formatDate, verdictColor } from '@/utils/format';
import { useToast } from '@/hooks/useToast';
import { config } from '@/config';
import type { AnalysisResponse } from '@/types/analysis';

export default function ResultsPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { addToast } = useToast();

  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    if (!id) {
      setNotFound(true);
      setLoading(false);
      return;
    }
    const r = getResult(id);
    if (r) {
      setResult(r);
    } else {
      setNotFound(true);
    }
    setLoading(false);
  }, [id]);

  const handleCopySummary = () => {
    if (!result) return;
    const summary = [
      `TruthLens AI — Analysis Summary`,
      `Verdict: ${result.verdict}`,
      result.confidence ? `Confidence: ${Math.round(result.confidence * 100)}%` : '',
      `Headline: ${result.headline}`,
      `Date: ${formatDate(result.created_at)}`,
      `Analysis ID: ${result.analysis_id}`,
      '',
      `Explanation: ${result.explanation}`,
    ]
      .filter(Boolean)
      .join('\n');

    navigator.clipboard
      .writeText(summary)
      .then(() => addToast('Summary copied to clipboard.', 'success'))
      .catch(() => addToast('Could not copy summary.', 'error'));
  };

  const handlePrint = () => {
    window.print();
  };

  if (loading) return <LoadingSkeleton />;

  if (notFound || !result) {
    return (
      <div className="mx-auto max-w-2xl">
        <ErrorState
          title="Analysis not found"
          message="This analysis result could not be found. It may have been cleared from your browser's local storage."
        />
        <div className="mt-4 text-center">
          <Link to="/analyze" className="btn-primary">
            <Search size={16} />
            Analyze News
          </Link>
        </div>
      </div>
    );
  }

  const colors = verdictColor(result.verdict);

  return (
    <div className="mx-auto max-w-5xl">
      <PageHeader
        title="Analysis Results"
        subtitle={`Analysis ID: ${result.analysis_id}`}
        icon={<Hash size={20} />}
        actions={
          <button
            type="button"
            onClick={() => navigate('/analyze')}
            className="btn-ghost"
          >
            <ArrowLeft size={16} />
            Back
          </button>
        }
      />

      {/* Main Verdict Card */}
      <div className={`glass-card mb-6 overflow-hidden p-6`}>
        <div className={`mb-4 h-1 w-full rounded-full bg-gradient-to-r ${colors.gradient}`} />
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex-1">
            <div className="mb-3 flex flex-wrap items-center gap-3">
              <VerdictBadge verdict={result.verdict} size="lg" />
              {config.demoMode && (
                <span className="rounded-full bg-amber-500/10 px-2.5 py-1 text-[10px] font-medium text-amber-400">
                  Sample Data
                </span>
              )}
            </div>
            <h2 className="mb-2 text-lg font-semibold text-slate-100">
              {result.headline}
            </h2>
            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500">
              <span className="flex items-center gap-1.5">
                <Clock size={12} />
                {formatDate(result.created_at)}
              </span>
              <span className="flex items-center gap-1.5">
                {result.mode === 'text_image' ? <ImageIcon size={12} /> : <FileText size={12} />}
                {result.mode === 'text_image' ? 'Text + Image' : 'Text Only'}
              </span>
              {result.source_url && (
                <a
                  href={result.source_url}
                  target="_blank"
                  rel="noopener noreferrer nofollow"
                  className="flex items-center gap-1.5 text-cyan-400 hover:text-cyan-300"
                >
                  <ExternalLink size={12} />
                  Source URL
                </a>
              )}
            </div>
          </div>
        </div>

        {typeof result.confidence === 'number' && (
          <div className="mt-5 max-w-md">
            <ConfidenceIndicator confidence={result.confidence} />
          </div>
        )}
      </div>

      {/* Analysis Cards */}
      <div className="mb-6 grid gap-4 lg:grid-cols-2">
        {result.text_analysis && <TextAnalysisCard result={result.text_analysis} />}

        {result.mode === 'text_image' && result.image_analysis && (
          <ImageAnalysisCard result={result.image_analysis} />
        )}

        {result.mode === 'text_image' && !result.image_analysis && (
          <div className="glass-card flex flex-col items-center justify-center p-5 text-center">
            <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-slate-500/10">
              <AlertTriangle size={18} className="text-slate-400" />
            </div>
            <h3 className="mb-1 text-sm font-semibold text-slate-200">Image Analysis Unavailable</h3>
            <p className="text-xs text-slate-500">
              No image analysis was returned for this submission.
            </p>
          </div>
        )}
      </div>

      {/* Evidence */}
      {result.evidence && result.evidence.length > 0 && (
        <div className="mb-6">
          <EvidenceList items={result.evidence} />
        </div>
      )}

      {/* Explanation */}
      <div className="mb-6">
        <ExplanationPanel
          explanation={result.explanation}
          evidence={result.evidence}
          limitations={
            result.verdict === 'UNVERIFIED'
              ? ['The system could not find sufficient evidence to verify or refute this claim.']
              : []
          }
        />
      </div>

      {/* Action Buttons */}
      <div className="flex flex-wrap gap-3">
        <Link to="/analyze" className="btn-primary">
          <Search size={16} />
          Analyze Another News Item
        </Link>
        <button type="button" onClick={handleCopySummary} className="btn-secondary">
          <Copy size={16} />
          Copy Summary
        </button>
        <button type="button" onClick={handlePrint} className="btn-secondary">
          <Printer size={16} />
          Print / Save Report
        </button>
        {result.evidence && result.evidence.length > 0 && (
          <button
            type="button"
            onClick={() => {
              result.evidence?.forEach((e) => {
                if (e.url) window.open(e.url, '_blank', 'noopener,nofollow');
              });
            }}
            className="btn-secondary"
          >
            <ExternalLink size={16} />
            Open All Sources
          </button>
        )}
      </div>
    </div>
  );
}
