export function PlayerCardSkeleton() {
  return (
    <div className="rounded-2xl border border-white/5 bg-white/[0.03] p-5 animate-pulse">
      <div className="flex items-start gap-4">
        <div className="h-16 w-16 rounded-xl bg-white/10" />
        <div className="flex-1 space-y-2">
          <div className="h-5 w-3/4 rounded bg-white/10" />
          <div className="h-4 w-1/2 rounded bg-white/10" />
        </div>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-3">
        <div className="h-12 rounded-lg bg-white/10" />
        <div className="h-12 rounded-lg bg-white/10" />
      </div>
    </div>
  )
}

export function PlayerGridSkeleton() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {Array.from({ length: 8 }).map((_, i) => (
        <PlayerCardSkeleton key={i} />
      ))}
    </div>
  )
}

export function LoadingOverlay({ message }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-16">
      <div className="relative h-12 w-12">
        <div className="absolute inset-0 rounded-full border-2 border-emerald-500/20" />
        <div className="absolute inset-0 animate-spin rounded-full border-2 border-transparent border-t-emerald-400" />
      </div>
      <p className="text-sm text-slate-400 animate-pulse">
        {message ?? 'AI đang phân tích hàng ngàn dữ liệu...'}
      </p>
    </div>
  )
}
