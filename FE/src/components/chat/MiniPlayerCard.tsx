import type { SimilarPlayer } from '../../types/player'
import { formatCurrency, formatPercent } from '../../utils/formatters'

export function MiniPlayerCard({ player }: { player: SimilarPlayer }) {
  const score = player.similarity_score <= 1 ? player.similarity_score : player.similarity_score / 100

  return (
    <div className="mt-2 flex items-center gap-3 rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-3">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-emerald-600/30 text-xs font-bold text-emerald-200">
        {player.name
          .split(' ')
          .map((w) => w[0])
          .slice(0, 2)
          .join('')}
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate font-semibold text-white text-sm">{player.name}</p>
        <p className="text-xs text-slate-400">
          {[player.position, player.league, player.age && `${player.age} tuổi`].filter(Boolean).join(' · ')}
        </p>
      </div>
      <div className="text-right shrink-0">
        <p className="text-sm font-bold text-emerald-400">{formatPercent(score)}</p>
        <p className="text-[10px] text-slate-500">tương đồng</p>
        <p className="text-xs font-medium text-slate-300">{formatCurrency(player.price)}</p>
      </div>
    </div>
  )
}
