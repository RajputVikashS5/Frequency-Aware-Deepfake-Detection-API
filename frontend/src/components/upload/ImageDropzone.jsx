import React, { useState, useRef } from 'react';
import { Upload, Image as ImageIcon } from 'lucide-react';
import { appConfig } from '../../config/appConfig';
import { validateFile } from '../../utils/fileValidation';

export default function ImageDropzone({ onFileSelected, onError }) {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleFiles = (fileList) => {
    if (!fileList || fileList.length === 0) return;
    const file = fileList[0];

    const validation = validateFile(file);
    if (!validation.isValid) {
      if (onError) onError(validation.error);
      return;
    }

    if (onFileSelected) onFileSelected(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  };

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragOver(true);
      }}
      onDragLeave={() => setIsDragOver(false)}
      onDrop={handleDrop}
      onClick={() => fileInputRef.current?.click()}
      className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all ${
        isDragOver
          ? 'border-accent-cyan bg-accent-cyan/5 scale-[1.005]'
          : 'border-border bg-card hover:border-accent-cyan/60 hover:bg-card-subtle'
      }`}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept={appConfig.allowedMimeTypes.join(',')}
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />

      <div className="flex flex-col items-center justify-center space-y-3">
        <div className="w-12 h-12 rounded-xl bg-card-subtle border border-border flex items-center justify-center text-accent-cyan">
          <Upload className="w-6 h-6" />
        </div>
        <div>
          <h3 className="font-semibold text-slate-100 text-sm">
            Drag and drop facial image here, or <span className="text-accent-cyan underline">browse</span>
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Supports JPEG, PNG, and WebP (up to 10 MB).
          </p>
        </div>
      </div>
    </div>
  );
}
