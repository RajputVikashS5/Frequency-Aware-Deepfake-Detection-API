import React from 'react';

export default function LoadingSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      {/* Top Banner Skeleton */}
      <div className="bg-card rounded-xl border border-border p-6 h-32 flex flex-col justify-between" />

      {/* Grid of 4 Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-card rounded-xl border border-border p-4 h-64 space-y-3">
            <div className="h-4 bg-card-subtle rounded w-3/4" />
            <div className="h-44 bg-canvas rounded" />
            <div className="h-3 bg-card-subtle rounded w-5/6" />
          </div>
        ))}
      </div>

      {/* Bottom Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-card rounded-xl border border-border p-6 h-56" />
        <div className="bg-card rounded-xl border border-border p-6 h-56" />
      </div>
    </div>
  );
}
