import {
  Info,
  Target,
  Network,
  FileText,
  Image as ImageIcon,
  GitMerge,
  BookOpen,
  Brain,
  BarChart3,
  AlertTriangle,
  ShieldCheck,
  ArrowRight,
} from 'lucide-react';
import PageHeader from '@/components/common/PageHeader';
import FeatureCard from '@/components/common/FeatureCard';

const architecture = [
  {
    icon: FileText,
    title: 'Text Analysis',
    description: 'A fine-tuned language model analyzes headline and article text for linguistic cues, emotional framing, source attribution patterns, and factual consistency.',
    accent: 'from-cyan-500 to-blue-600',
  },
  {
    icon: ImageIcon,
    title: 'Image Analysis',
    description: 'A vision model examines uploaded images for digital manipulation artifacts, metadata inconsistencies, and visual-context mismatches with the text.',
    accent: 'from-violet-500 to-purple-600',
  },
  {
    icon: GitMerge,
    title: 'Multimodal Fusion',
    description: 'Text and image model outputs are combined using a fusion strategy that leverages cross-modal consistency to produce a unified prediction.',
    accent: 'from-emerald-500 to-teal-600',
  },
  {
    icon: BookOpen,
    title: 'Evidence Retrieval',
    description: 'Relevant source articles are retrieved and compared against the submitted claim to provide corroborating or contradicting evidence.',
    accent: 'from-amber-500 to-orange-600',
  },
  {
    icon: Brain,
    title: 'Explainable AI',
    description: 'The system surfaces which factors influenced each prediction, separating model-derived signals from verified evidence sources.',
    accent: 'from-rose-500 to-red-600',
  },
];

const metrics = [
  { label: 'Accuracy', description: 'Overall proportion of correct predictions across all classes.' },
  { label: 'Precision', description: 'Proportion of predicted positives that are actually positive.' },
  { label: 'Recall', description: 'Proportion of actual positives correctly identified by the model.' },
  { label: 'Macro-F1', description: 'Balanced F1 score averaged across all classes, treating each class equally.' },
];

const pipeline = [
  { label: 'News Input', icon: FileText },
  { label: 'Text & Image Processing', icon: ImageIcon },
  { label: 'Model Predictions', icon: Brain },
  { label: 'Evidence Assessment', icon: BookOpen },
  { label: 'Explainable Result', icon: ShieldCheck },
];

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader
        title="About & Methodology"
        subtitle="Understanding the TruthLens AI system architecture and approach."
        icon={<Info size={20} />}
      />

      <section className="mb-6">
        <div className="glass-card p-5">
          <div className="mb-3 flex items-center gap-2">
            <Target size={16} className="text-cyan-400" />
            <h2 className="section-title">Project Motivation</h2>
          </div>
          <p className="text-sm leading-relaxed text-slate-400">
            The rapid spread of misinformation through social media and online platforms has become
            a critical societal challenge. Manual fact-checking cannot keep up with the volume of
            content published daily. TruthLens AI aims to provide an automated, transparent, and
            evidence-grounded approach to assist human fact-checkers and inform readers.
          </p>
        </div>
      </section>

      <section className="mb-6">
        <div className="glass-card p-5">
          <div className="mb-3 flex items-center gap-2">
            <AlertTriangle size={16} className="text-cyan-400" />
            <h2 className="section-title">Research Problem</h2>
          </div>
          <p className="text-sm leading-relaxed text-slate-400">
            Existing fake news detection systems often rely on single-modality analysis (text only)
            and operate as black boxes, offering predictions without explanation. This project
            addresses two gaps: (1) combining text and image analysis for multimodal detection, and
            (2) providing explainable, evidence-grounded reasoning for each prediction.
          </p>
        </div>
      </section>

      <section className="mb-6">
        <div className="mb-3 flex items-center gap-2">
          <Network size={16} className="text-cyan-400" />
          <h2 className="section-title">System Architecture</h2>
        </div>

        <div className="glass-card mb-4 p-5">
          <div className="flex flex-col items-stretch gap-3 lg:flex-row lg:items-center">
            {pipeline.map((step, i) => (
              <div key={step.label} className="flex items-center gap-3 lg:flex-1">
                <div className="flex flex-1 items-center gap-3 rounded-xl border border-white/10 bg-white/5 px-3 py-2.5">
                  <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-cyan-500/20 to-blue-500/10">
                    <step.icon size={14} className="text-cyan-400" />
                  </div>
                  <p className="text-xs font-medium text-slate-200">{step.label}</p>
                </div>
                {i < pipeline.length - 1 && (
                  <ArrowRight size={14} className="hidden flex-shrink-0 text-slate-600 lg:block" />
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {architecture.map((a) => (
            <FeatureCard
              key={a.title}
              icon={a.icon}
              title={a.title}
              description={a.description}
              accent={a.accent}
            />
          ))}
        </div>
      </section>

      <section className="mb-6">
        <div className="mb-3 flex items-center gap-2">
          <BarChart3 size={16} className="text-cyan-400" />
          <h2 className="section-title">Evaluation Metrics</h2>
        </div>
        <div className="glass-card p-5">
          <div className="grid gap-4 sm:grid-cols-2">
            {metrics.map((m) => (
              <div key={m.label} className="rounded-xl border border-white/10 bg-white/5 p-4">
                <p className="mb-1 text-sm font-semibold text-slate-100">{m.label}</p>
                <p className="text-xs leading-relaxed text-slate-400">{m.description}</p>
              </div>
            ))}
          </div>
          <p className="mt-4 text-xs text-slate-500">
            A confusion matrix is also used to visualize per-class performance and identify
            misclassification patterns between Real, Fake, Misleading, and Unverified categories.
          </p>
        </div>
      </section>

      <section className="mb-6">
        <div className="glass-card p-5">
          <div className="mb-3 flex items-center gap-2">
            <AlertTriangle size={16} className="text-amber-400" />
            <h2 className="section-title">Limitations & Ethical Considerations</h2>
          </div>
          <ul className="space-y-2 text-sm text-slate-400">
            <li className="flex items-start gap-2">
              <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-amber-400" />
              Automated predictions are not definitive proof of truth or falsity — they are advisory signals for human reviewers.
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-amber-400" />
              Model performance depends on training data coverage; novel misinformation tactics may not be detected.
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-amber-400" />
              Confidence scores reflect model certainty, not the probability that a claim is objectively true.
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-amber-400" />
              The system should not be used as the sole basis for content moderation or censorship decisions.
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-amber-400" />
              Dataset and model details will be documented here once confirmed by the research team.
            </li>
          </ul>
        </div>
      </section>
    </div>
  );
}
