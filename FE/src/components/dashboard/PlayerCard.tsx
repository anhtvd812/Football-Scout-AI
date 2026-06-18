import type { Player } from '../../types/player'
import { formatCurrency } from '../../utils/formatters'
import { StatusBadge } from '../ui/StatusBadge'

interface PlayerCardProps {
  player: Player
  onClick: () => void
}

function PlayerAvatar({ name }: { name: string }) {
  const initials = name
    .split(' ')
    .map((w) => w[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()

  return (
    <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-600/40 to-emerald-900/60 text-lg font-bold text-emerald-100 ring-1 ring-emerald-500/30">
      {initials}
    </div>
  )
}

export function PlayerCard({ player, onClick }: PlayerCardProps) {
  const diff = player.predicted_value_eur - player.actual_market_value_eur
  const diffPct = Math.round((diff / player.actual_market_value_eur) * 100)

  return (
    <button
      type="button"
      onClick={onClick}
      className="group w-full rounded-2xl border border-white/10 bg-white/[0.03] p-5 text-left transition hover:border-emerald-500/30 hover:bg-white/[0.06] hover:shadow-lg hover:shadow-emerald-500/5"
    >
      <div className="flex items-start gap-4">
        <PlayerAvatar name={player.player_name} />
        <div className="min-w-0 flex-1">
          <h3 className="truncate font-semibold text-white group-hover:text-emerald-300 transition">
            {player.player_name}
          </h3>
          <p className="text-sm text-slate-400">
            {player.position} · {player.league} · {player.age} tuổi
          </p>
          <div className="mt-2">
            <StatusBadge status={player.market_status} />
          </div>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3">
        <div className="rounded-xl bg-black/30 px-3 py-2">
          <p className="text-[10px] uppercase tracking-wider text-slate-500">Giá thị trường</p>
          <p className="text-sm font-bold text-slate-200">{formatCurrency(player.actual_market_value_eur)}</p>
        </div>
        <div className="rounded-xl bg-emerald-500/10 px-3 py-2 ring-1 ring-emerald-500/20">
          <p className="text-[10px] uppercase tracking-wider text-emerald-500/80">AI dự đoán</p>
          <p className="text-sm font-bold text-emerald-300">{formatCurrency(player.predicted_value_eur)}</p>
        </div>
      </div>

      {player.market_status !== 'Fair' && (
        <p className={`mt-2 text-xs font-medium ${diff > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
          {diff > 0 ? '↑' : '↓'} {Math.abs(diffPct)}% so với thị trường
        </p>
      )}
    </button>
  )
}
