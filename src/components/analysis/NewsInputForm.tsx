import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Search, RotateCcw, Loader2, Link2, Type, ImagePlus } from 'lucide-react';
import ImageUploader from '@/components/analysis/ImageUploader';
import { config } from '@/config';
import type { AnalysisMode } from '@/types/analysis';

const schema = z.object({
  headline: z.string().min(1, 'Headline is required').max(300, 'Headline is too long (max 300 characters)'),
  article_text: z.string().min(20, 'Article text must be at least 20 characters').max(20000, 'Article text is too long (max 20,000 characters)'),
  source_url: z.string().url('Enter a valid URL').optional().or(z.literal('')),
});

type FormValues = z.infer<typeof schema>;

export interface NewsFormValues extends FormValues {
  image: File | null;
  mode: AnalysisMode;
}

interface NewsInputFormProps {
  onSubmit: (values: NewsFormValues) => void;
  isSubmitting: boolean;
  defaultMode?: AnalysisMode;
}

export default function NewsInputForm({
  onSubmit,
  isSubmitting,
  defaultMode = config.defaultMode,
}: NewsInputFormProps) {
  const [mode, setMode] = useState<AnalysisMode>(defaultMode);
  const [image, setImage] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [imageError, setImageError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      headline: '',
      article_text: '',
      source_url: '',
    },
  });

  const headlineValue = watch('headline') ?? '';
  const articleValue = watch('article_text') ?? '';

  const handleImageSelect = (file: File | null) => {
    setImageError(null);
    setImage(file);
    if (file) {
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    } else {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
  };

  const handleFormSubmit = (values: FormValues) => {
    if (mode === 'text_image' && !image) {
      setImageError('Text + Image mode requires an image. Switch to Text Only mode or upload an image.');
      return;
    }
    setImageError(null);
    onSubmit({
      ...values,
      source_url: values.source_url || undefined,
      image: mode === 'text_image' ? image : null,
      mode,
    });
  };

  const handleClear = () => {
    reset();
    setImage(null);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    setImageError(null);
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-5">
      <div className="flex gap-2 rounded-xl border border-white/10 bg-white/5 p-1">
        <button
          type="button"
          onClick={() => setMode('text_image')}
          className={`flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-all ${
            mode === 'text_image'
              ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/15 text-cyan-300'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <ImagePlus size={16} />
          Text + Image
        </button>
        <button
          type="button"
          onClick={() => {
            setMode('text_only');
            if (image) handleImageSelect(null);
          }}
          className={`flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-all ${
            mode === 'text_only'
              ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/15 text-cyan-300'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Type size={16} />
          Text Only
        </button>
      </div>

      <div>
        <label htmlFor="headline" className="label-text">
          News Headline <span className="text-red-400">*</span>
        </label>
        <input
          id="headline"
          type="text"
          {...register('headline')}
          disabled={isSubmitting}
          className="input-field"
          placeholder="Enter the news headline to analyze..."
          aria-invalid={!!errors.headline}
          aria-describedby={errors.headline ? 'headline-error' : undefined}
        />
        <div className="mt-1.5 flex items-center justify-between">
          {errors.headline ? (
            <p id="headline-error" className="text-xs text-red-400" role="alert">
              {errors.headline.message}
            </p>
          ) : (
            <span />
          )}
          <span className="text-xs text-slate-500">{headlineValue.length}/300</span>
        </div>
      </div>

      <div>
        <label htmlFor="article_text" className="label-text">
          Article Text <span className="text-red-400">*</span>
        </label>
        <textarea
          id="article_text"
          rows={6}
          {...register('article_text')}
          disabled={isSubmitting}
          className="input-field resize-y"
          placeholder="Paste the full article text here..."
          aria-invalid={!!errors.article_text}
          aria-describedby={errors.article_text ? 'article-error' : undefined}
        />
        <div className="mt-1.5 flex items-center justify-between">
          {errors.article_text ? (
            <p id="article-error" className="text-xs text-red-400" role="alert">
              {errors.article_text.message}
            </p>
          ) : (
            <span />
          )}
          <span className="text-xs text-slate-500">{articleValue.length}/20000</span>
        </div>
      </div>

      <div>
        <label htmlFor="source_url" className="label-text">
          Source URL <span className="text-slate-600">(optional)</span>
        </label>
        <div className="relative">
          <Link2 size={16} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            id="source_url"
            type="url"
            {...register('source_url')}
            disabled={isSubmitting}
            className="input-field pl-10"
            placeholder="https://example.com/article..."
            aria-invalid={!!errors.source_url}
            aria-describedby={errors.source_url ? 'url-error' : undefined}
          />
        </div>
        {errors.source_url && (
          <p id="url-error" className="mt-1.5 text-xs text-red-400" role="alert">
            {errors.source_url.message}
          </p>
        )}
      </div>

      {mode === 'text_image' && (
        <div>
          <label className="label-text">
            Related Image <span className="text-slate-600">(required for Text + Image mode)</span>
          </label>
          <ImageUploader
            image={image}
            previewUrl={previewUrl}
            onImageSelect={handleImageSelect}
            onError={(msg) => setImageError(msg)}
            disabled={isSubmitting}
          />
          {imageError && (
            <p className="mt-2 text-xs text-red-400" role="alert">
              {imageError}
            </p>
          )}
          {!image && !imageError && (
            <p className="mt-2 text-xs text-amber-400/80">
              No image uploaded yet. Switch to Text Only mode if you don't have one.
            </p>
          )}
        </div>
      )}

      <div className="flex flex-col gap-3 sm:flex-row">
        <button type="submit" disabled={isSubmitting} className="btn-primary flex-1">
          {isSubmitting ? (
            <>
              <Loader2 size={16} className="animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <Search size={16} />
              Analyze News
            </>
          )}
        </button>
        <button
          type="button"
          onClick={handleClear}
          disabled={isSubmitting}
          className="btn-secondary"
        >
          <RotateCcw size={16} />
          Clear Form
        </button>
      </div>
    </form>
  );
}
