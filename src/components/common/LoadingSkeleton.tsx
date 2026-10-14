export default function LoadingSkeleton() {
  return (
    <div className="space-y-4">
      <div className="glass-card p-6">
        <div className="mb-4 h-6 w-48 animate-pulse rounded-lg bg-white/10" />
        <div className="mb-3 h-4 w-full animate-pulse rounded bg-white/5" />
        <div className="mb-3 h-4 w-3/4 animate-pulse rounded bg-white/5" />
        <div className="h-4 w-1/2 animate-pulse rounded bg-white/5" />
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="glass-card p-5">
          <div className="mb-3 h-5 w-32 animate-pulse rounded bg-white/10" />
          <div className="mb-2 h-3 w-full animate-pulse rounded bg-white/5" />
          <div className="mb-2 h-3 w-5/6 animate-pulse rounded bg-white/5" />
          <div className="h-3 w-2/3 animate-pulse rounded bg-white/5" />
        </div>
        <div className="glass-card p-5">
          <div className="mb-3 h-5 w-28 animate-pulse rounded bg-white/10" />
          <div className="mb-2 h-3 w-full animate-pulse rounded bg-white/5" />
          <div className="mb-2 h-3 w-4/5 animate-pulse rounded bg-white/5" />
          <div className="h-3 w-1/2 animate-pulse rounded bg-white/5" />
        </div>
      </div>
    </div>
  );
}
