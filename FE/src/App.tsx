import { useCallback, useEffect, useState } from 'react'
import type { Player, PlayerFilters } from './types/player'
import { getPlayers } from './api/players'
import { Header } from './components/layout/Header'
import { FilterBar } from './components/dashboard/FilterBar'
import { PlayerGrid } from './components/dashboard/PlayerGrid'
import { PlayerDetailModal } from './components/dashboard/PlayerDetailModal'
import { ChatWidget } from './components/chat/ChatWidget'
import { ToastProvider, useToast } from './components/ui/Toast'

const DEFAULT_FILTERS: PlayerFilters = {
  search: '',
  position: 'Tất cả',
  league: 'Tất cả',
  minAge: 16,
  maxAge: 35,
  maxBudget: 100_000_000,
}

function Dashboard() {
  const [filters, setFilters] = useState<PlayerFilters>(DEFAULT_FILTERS)
  const [players, setPlayers] = useState<Player[]>([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<Player | null>(null)
  const { toast } = useToast()

  const fetchPlayers = useCallback(async (f: PlayerFilters) => {
    setLoading(true)
    try {
      const data = await getPlayers(f)
      setPlayers(data)
    } catch {
      toast('Lỗi khi tải danh sách cầu thủ. API có thể chưa sẵn sàng.', 'error')
      setPlayers([])
    } finally {
      setLoading(false)
    }
  }, [toast])

  useEffect(() => {
    fetchPlayers(DEFAULT_FILTERS)
  }, [fetchPlayers])

  return (
    <div className="min-h-screen bg-[#0a0f0d]">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_at_top,_rgba(16,185,129,0.08)_0%,_transparent_50%)]" />
      <Header />

      <main className="relative mx-auto max-w-7xl px-4 py-8 sm:px-6 space-y-8">
        <section>
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-white">Khám phá & Định giá</h2>
            <p className="mt-1 text-sm text-slate-400">
              Tra cứu cầu thủ, so sánh giá thị trường với dự đoán AI và phát hiện hidden gem.
            </p>
          </div>
          <FilterBar
            filters={filters}
            onChange={setFilters}
            onSearch={() => fetchPlayers(filters)}
            loading={loading}
          />
        </section>

        <section>
          <PlayerGrid players={players} loading={loading} onSelect={setSelected} />
        </section>
      </main>

      <PlayerDetailModal player={selected} onClose={() => setSelected(null)} />
      <ChatWidget />
    </div>
  )
}

export default function App() {
  return (
    <ToastProvider>
      <Dashboard />
    </ToastProvider>
  )
}
