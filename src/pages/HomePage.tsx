import { Link } from 'react-router-dom';
import {
  Search,
  FileText,
  Image as ImageIcon,
  BookOpen,
  Brain,
  ArrowRight,
  ShieldCheck,
  Info,
  Workflow,
} from 'lucide-react';
import FeatureCard from '@/components/common/FeatureCard';
import { config } from '@/config';
import { getHistory } from '@/utils/history';
import { formatDate, verdictColor } from '@/utils/format';

const features = [
  {
    icon: FileText,
    title: 'Text Analysis',
    description: 'Linguistic and semantic analysis of headlines and article body text to detect misinformation patterns.',
    accent: 'from-cyan-500 to-blue-600',
  },
  {
    icon: ImageIcon,
    title: 'Image Analysis',
    description: 'Visual manipulation detection and image-text consistency checking to spot doctored or miscontextualized images.',
    accent: 'from-violet-500 to-purple-600',
  },
  {
    icon: BookOpen,
    title: 'Evidence Retrieval',
    description: 'Retrieval of relevant source articles to corroborate or contradict claims with real-world evidence.',
    accent: 'from-emerald-500 to-teal-600',
  },
  {
    icon: Brain,
    title: 'Explainable AI',
    description: 'Transparent reasoning that shows which factors contributed to each prediction, not just a black-box label.',
    accent: 'from-amber-500 to-orange-600',
  },
];

const pipeline = [
  { label: 'News Input', icon: Search },
  { label: 'Text & Image Processing', icon: FileText },
  { label: 'Model Predictions', icon: Brain },
  { label: 'Evidence Assessment', icon: BookOpen },
  { label: 'Explainable Result', icon: ShieldCheck },
];

export default function HomePage() {
  const history = getHistory().slice(0, 3);

  return (
    <div className="mx-auto max-w-6xl">
      <section className="mb-10 text-center">
        <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-500/10 px-4 py-1.5">
          <ShieldCheck size={14} className="text-cyan-400" />
          <span className="text-xs font-medium text-cyan-300">Multimodal Fake News Detection</span>
        </div>
        <h1 className="mb-3 text-3xl font-bold leading-tight text-slate-100 sm:text-4xl md:text-5xl">
          Detect Fake News with the
          <br />
          <span className="gradient-text">Power of AI</span>
        </h1>
        <p className="mx-auto mb-6 max-w-2xl text-sm leading-relaxed text-slate-400 sm:text-base">
          TruthLens AI combines text analysis, image forensics, evidence retrieval, and explainable
          AI to help you assess the credibility of news articles with transparency and evidence-grounded reasoning.
        </p>
        <div className="flex flex-col items-center justify-center gap-3 sm:flex-row">
          <Link to="/analyze" className="btn-primary">
            <Search size={16} />
            Analyze News
          </Link>
          <Link to="/about" className="btn-secondary">
            <Info size={16} />
            Explore How It Works
          </Link>
        </div>
      </section>

      <section className="mb-10">
        <h2 className="mb-4 text-lg font-semibold text-slate-100">Core Capabilities</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {features.map((f) => (
            <FeatureCard
              key={f.title}
              icon={f.icon}
              title={f.title}
              description={f.description}
              accent={f.accent}
            />
          ))}
        </div>
      </section>

      <section className="mb-10">
        <h2 className="mb-4 text-lg font-semibold text-slate-100">Verification Pipeline</h2>
        <div className="glass-card p-6">
          <div className="flex flex-col items-stretch gap-3 lg:flex-row lg:items-center">
            {pipeline.map((step, i) => (
              <div key={step.label} className="flex items-center gap-3 lg:flex-1">
                <div className="flex flex-1 items-center gap-3 rounded-xl border border-white/10 bg-white/5 px-4 py-3">
                  <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-cyan-500/20 to-blue-500/10">
                    <step.icon size={16} className="text-cyan-400" />
                  </div>
                  <div>
                    <p className="text-xs text-slate-500">Step {i + 1}</p>
                    <p className="text-sm font-medium text-slate-200">{step.label}</p>
                  </div>
                </div>
                {i < pipeline.length - 1 && (
                  <ArrowRight size={16} className="hidden flex-shrink-0 text-slate-600 lg:block" />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {history.length > 0 && (
        <section className="mb-10">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-100">Recent Analyses</h2>
            <Link to="/history" className="text-xs font-medium text-cyan-400 hover:text-cyan-300">
              View all
            </Link>
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            {history.map((entry) => {
              const colors = verdictColor(entry.verdict);
              return (
                <Link
                  key={entry.analysis_id}
                  to={`/results/${entry.analysis_id}`}
                  className="glass-card-hover p-4"
                >
                  <div className="mb-2 flex items-center gap-2">
                    <div className={`h-8 w-1 rounded-full bg-gradient-to-b ${colors.gradient}`} />
                    <span className={`text-xs font-semibold ${colors.text}`}>{entry.verdict}</span>
                  </div>
                  <p className="mb-2 line-clamp-2 text-sm font-medium text-slate-200">
                    {entry.headline}
                  </p>
                  <p className="text-xs text-slate-500">{formatDate(entry.created_at)}</p>
                </Link>
              );
            })}
          </div>
        </section>
      )}

      <section className="mb-4">
        <div className="flex items-start gap-3 rounded-2xl border border-amber-500/20 bg-amber-500/5 p-4">
          <Info size={18} className="mt-0.5 flex-shrink-0 text-amber-400" />
          <div>
            <p className="text-sm font-medium text-amber-400">Important Disclaimer</p>
            <p className="mt-1 text-xs leading-relaxed text-slate-400">
              TruthLens AI provides automated predictions to assist with news verification. These
              predictions are not definitive proof of truth or falsity. Always verify claims with
              primary sources and use human judgment. {config.demoMode && 'Currently running in Demo Mode with sample data.'}
            </p>
          </div>
        </div>
      </section>

      <div className="flex flex-col items-center gap-3 rounded-2xl border border-white/10 bg-gradient-to-br from-cyan-500/5 to-blue-500/5 p-8 text-center">
        <Workflow size={28} className="text-cyan-400" />
        <h2 className="text-xl font-bold text-slate-100">Ready to verify a news article?</h2>
        <p className="max-w-md text-sm text-slate-400">
          Submit a headline, article text, and an optional image to get started.
        </p>
        <Link to="/analyze" className="btn-primary">
          <Search size={16} />
          Start Analysis
        </Link>
      </div>
    </div>
  );
}
