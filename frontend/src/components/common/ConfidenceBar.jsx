import React from 'react';

export default function ConfidenceBar({ percentage, isManipulated }) {
  const cleanVal = Math.min(100, Math.max(0, Number(percentage) || 0));

  return (
    <div className="w-full space-y-1">
      <div className="w-full bg-canvas rounded-full h-2 overflow-hidden border border-border">
        <div
          className={`h-full transition-all duration-700 rounded-full ${
            isManipulated ? 'bg-red-500' : 'bg-emerald-500'
          }`}
          style={{ width: `${cleanVal}%` }}
        />
      </div>
    </div>
  );
}
