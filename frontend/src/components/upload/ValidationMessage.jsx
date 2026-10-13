import React from 'react';
import { AlertCircle } from 'lucide-react';

export default function ValidationMessage({ message }) {
  if (!message) return null;

  return (
    <div className="bg-red-950/30 border border-red-900/60 rounded-lg p-3 flex items-start space-x-2.5 text-xs text-red-300 animate-fadeIn">
      <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
      <span className="leading-relaxed">{message}</span>
    </div>
  );
}
