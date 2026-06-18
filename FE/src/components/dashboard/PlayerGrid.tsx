import type { Player } from '../../types/player'
import { PlayerCard } from './PlayerCard'
import { PlayerGridSkeleton } from '../ui/Loading'

interface PlayerGridProps {
  players: Player[]
  loading: boolean
  onSelect: (player: Player) => void
}

export function PlayerGrid({ players, loading, onSelect }: PlayerGridProps) {
  if (loading) return <PlayerGridSkeleton />

  if (players.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-white/10 py-16 text-center">
        <p className="text-4xl mb-3">⚽</p>
        <p className="text-slate-300 font-medium">Không tìm thấy cầu thủ phù hợp</p>
        <p className="mt-1 text-sm text-slate-500">Thử điều chỉnh bộ lọc hoặc hỏi Trợ lý AI</p>
      </div>
    )
  }

  return (
    <div>
      <p className="mb-4 text-sm text-slate-400">
        Hiển thị <span className="font-semibold text-emerald-400">{players.length}</span> cầu thủ
      </p>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {players.map((p) => (
          <PlayerCard key={p.id} player={p} onClick={() => onSelect(p)} />
        ))}
      </div>
    </div>
  )
}
