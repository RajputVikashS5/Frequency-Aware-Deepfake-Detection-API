import { useCallback, useRef, useState } from 'react';
import { UploadCloud, X, ImageIcon, AlertCircle } from 'lucide-react';
import { config } from '@/config';

interface ImageUploaderProps {
  image: File | null;
  previewUrl: string | null;
  onImageSelect: (file: File | null) => void;
  onError: (message: string) => void;
  disabled?: boolean;
}

export default function ImageUploader({
  image,
  previewUrl,
  onImageSelect,
  onError,
  disabled,
}: ImageUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateFile = useCallback(
    (file: File): boolean => {
      if (!config.acceptedImageTypes.includes(file.type)) {
        onError(
          `Unsupported file type. Please upload ${config.acceptedImageExtensions.join(', ').toUpperCase()} files.`
        );
        return false;
      }
      if (file.size > config.maxImageSizeBytes) {
        onError(`File is too large. Maximum size is ${config.maxImageSizeBytes / (1024 * 1024)} MB.`);
        return false;
      }
      return true;
    },
    [onError]
  );

  const handleFile = useCallback(
    (file: File | null) => {
      if (!file) return;
      if (validateFile(file)) {
        onImageSelect(file);
      }
    },
    [onImageSelect, validateFile]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      if (disabled) return;
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile, disabled]
  );

  const handleDragOver = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      if (!disabled) setIsDragging(true);
    },
    [disabled]
  );

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0] ?? null;
      handleFile(file);
      e.target.value = '';
    },
    [handleFile]
  );

  const handleRemove = useCallback(() => {
    onImageSelect(null);
    if (inputRef.current) inputRef.current.value = '';
  }, [onImageSelect]);

  if (image && previewUrl) {
    return (
      <div className="glass-card overflow-hidden p-4">
        <div className="relative">
          <img
            src={previewUrl}
            alt="Uploaded preview"
            className="max-h-64 w-full rounded-xl object-contain"
          />
          <button
            type="button"
            onClick={handleRemove}
            disabled={disabled}
            className="absolute right-2 top-2 flex h-8 w-8 items-center justify-center rounded-lg bg-black/60 text-white backdrop-blur-md transition-colors hover:bg-red-600 disabled:opacity-50"
            aria-label="Remove image"
          >
            <X size={16} />
          </button>
        </div>
        <div className="mt-3 flex items-center gap-2 text-xs text-slate-400">
          <ImageIcon size={14} />
          <span className="truncate">{image.name}</span>
          <span className="flex-shrink-0">({(image.size / 1024).toFixed(0)} KB)</span>
        </div>
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          disabled={disabled}
          className="mt-2 text-xs font-medium text-cyan-400 hover:text-cyan-300 disabled:opacity-50"
        >
          Replace image
        </button>
        <input
          ref={inputRef}
          type="file"
          accept={config.acceptedImageTypes.join(',')}
          onChange={handleInputChange}
          disabled={disabled}
          className="hidden"
          aria-label="Browse for image file"
        />
      </div>
    );
  }

  return (
    <div
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onClick={() => !disabled && inputRef.current?.click()}
      onKeyDown={(e) => {
        if ((e.key === 'Enter' || e.key === ' ') && !disabled) {
          e.preventDefault();
          inputRef.current?.click();
        }
      }}
      role="button"
      tabIndex={0}
      aria-label="Upload image: click or drag and drop"
      className={`flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-10 text-center transition-all duration-200 ${
        isDragging
          ? 'border-cyan-400/60 bg-cyan-500/5'
          : 'border-white/15 bg-white/[0.02] hover:border-white/25 hover:bg-white/[0.04]'
      } ${disabled ? 'cursor-not-allowed opacity-50' : ''}`}
    >
      <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-500/10">
        <UploadCloud size={22} className="text-cyan-400" />
      </div>
      <p className="text-sm font-medium text-slate-300">
        Drag and drop an image, or{' '}
        <span className="text-cyan-400">click to browse</span>
      </p>
      <p className="mt-1.5 text-xs text-slate-500">
        {config.acceptedImageExtensions.join(', ').toUpperCase()} up to{' '}
        {config.maxImageSizeBytes / (1024 * 1024)} MB
      </p>
      <div className="mt-3 flex items-center gap-1.5 text-xs text-slate-600">
        <AlertCircle size={12} />
        <span>Optional — analysis works without an image</span>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept={config.acceptedImageTypes.join(',')}
        onChange={handleInputChange}
        disabled={disabled}
        className="hidden"
        aria-label="Browse for image file"
      />
    </div>
  );
}
