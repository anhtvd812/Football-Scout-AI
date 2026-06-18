import type { MarketStatus } from '../../types/player'
import { cn } from '../../utils/formatters'

const styles: Record<MarketStatus, string> = {
  Undervalued: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
  Fair: 'bg-slate-500/20 text-slate-300 border-slate-500/40',
  Overvalued: 'bg-red-500/20 text-red-300 border-red-500/40',
}

const labels: Record<MarketStatus, string> = {
  Undervalued: 'Món hời',
  Fair: 'Hợp lý',
  Overvalued: 'Bơm thổi',
}

export function StatusBadge({ status }: { status: MarketStatus }) {
  return (
    <span className={cn('inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold', styles[status])}>
      {labels[status]}
    </span>
  )
}
