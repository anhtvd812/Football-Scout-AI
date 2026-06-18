import { useEffect } from 'react'
import type { Player } from '../../types/player'
import { formatCurrency } from '../../utils/formatters'
import { StatusBadge } from '../ui/StatusBadge'
import { RadarChart } from './RadarChart'

interface PlayerDetailModalProps {
  player: Player | null
  onClose: () => void
}

export function PlayerDetailModal({ player, onClose }: PlayerDetailModalProps) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    if (player) {
      document.body.style.overflow = 'hidden'
      window.addEventListener('keydown', onKey)
    }
    return () => {
      document.body.style.overflow = ''
      window.removeEventListener('keydown', onKey)
    }
  }, [player, onClose])

  if (!player) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <button
        type="button"
        aria-label="Đóng"
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="relative max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl border border-white/10 bg-slate-950 shadow-2xl">
        <div className="sticky top-0 flex items-center justify-between border-b border-white/10 bg-slate-950/95 px-6 py-4 backdrop-blur">
          <div>
            <h2 className="text-xl font-bold text-white">{player.player_name}</h2>
            <p className="text-sm text-slate-400">
              {player.position} · {player.league} · {player.nationality} · {player.age} tuổi
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-2 text-slate-400 hover:bg-white/10 hover:text-white"
          >
            ✕
          </button>
        </div>

        <div className="p-6 space-y-6">
          <div className="flex flex-wrap items-center gap-3">
            <StatusBadge status={player.market_status} />
          </div>

          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
            <StatBox label="Giá thị trường" value={formatCurrency(player.actual_market_value_eur)} />
            <StatBox label="AI dự đoán" value={formatCurrency(player.predicted_value_eur)} highlight />
            <StatBox
              label="Chênh lệch"
              value={formatCurrency(player.predicted_value_eur - player.actual_market_value_eur)}
              highlight={player.market_status === 'Undervalued'}
            />
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-4">
            <h3 className="mb-4 text-center text-sm font-semibold uppercase tracking-wider text-slate-400">
              Biểu đồ kỹ năng
              {player.compare_with && ` · So với ${player.compare_with.name}`}
            </h3>
            <RadarChart
              playerStats={player.stats}
              compareStats={player.compare_with?.stats}
              playerName={player.player_name}
              compareName={player.compare_with?.name}
            />
          </div>

          {player.similar_players && player.similar_players.length > 0 && (
            <div>
              <h3 className="mb-3 text-sm font-semibold text-slate-300">Cầu thủ tương đồng</h3>
              <div className="space-y-2">
                {player.similar_players.map((s) => (
                  <div
                    key={s.name}
                    className="flex items-center justify-between rounded-xl border border-white/5 bg-black/20 px-4 py-3"
                  >
                    <div>
                      <p className="font-medium text-white">{s.name}</p>
                      <p className="text-xs text-slate-400">
                        {s.position} · {s.league} · {s.age} tuổi
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-bold text-emerald-400">
                        {Math.round(s.similarity_score * 100)}% tương đồng
                      </p>
                      <p className="text-xs text-slate-400">{formatCurrency(s.price)}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function StatBox({
  label,
  value,
  highlight,
}: {
  label: string
  value: string
  highlight?: boolean
}) {
  return (
    <div
      className={`rounded-xl px-4 py-3 ${highlight ? 'bg-emerald-500/10 ring-1 ring-emerald-500/20' : 'bg-black/30'}`}
    >
      <p className="text-[10px] uppercase tracking-wider text-slate-500">{label}</p>
      <p className={`text-lg font-bold ${highlight ? 'text-emerald-300' : 'text-white'}`}>{value}</p>
    </div>
  )
}
