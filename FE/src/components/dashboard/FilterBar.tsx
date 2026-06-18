import type { PlayerFilters } from '../../types/player'
import { LEAGUES, POSITIONS } from '../../api/mockData'
import { formatCurrency } from '../../utils/formatters'

interface FilterBarProps {
  filters: PlayerFilters
  onChange: (filters: PlayerFilters) => void
  onSearch: () => void
  loading?: boolean
}

export function FilterBar({ filters, onChange, onSearch, loading }: FilterBarProps) {
  const set = <K extends keyof PlayerFilters>(key: K, value: PlayerFilters[K]) => {
    onChange({ ...filters, [key]: value })
  }

  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 backdrop-blur-sm">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">Bộ lọc nâng cao</h2>
        <button
          type="button"
          onClick={onSearch}
          disabled={loading}
          className="rounded-xl bg-emerald-500 px-5 py-2 text-sm font-semibold text-emerald-950 transition hover:bg-emerald-400 disabled:opacity-50"
        >
          {loading ? 'Đang tìm...' : 'Tìm kiếm'}
        </button>
      </div>

      <div className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <div className="lg:col-span-2">
            <label className="mb-1.5 block text-xs font-medium text-slate-400">Tên cầu thủ / CLB</label>
            <input
              type="text"
              value={filters.search}
              onChange={(e) => set('search', e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && onSearch()}
              placeholder="VD: Simons, Premier League..."
              className="w-full rounded-xl border border-white/10 bg-black/30 px-4 py-2.5 text-sm text-white placeholder:text-slate-500 focus:border-emerald-500/50 focus:outline-none focus:ring-1 focus:ring-emerald-500/30"
            />
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-medium text-slate-400">Vị trí</label>
            <select
              value={filters.position}
              onChange={(e) => set('position', e.target.value)}
              className="w-full rounded-xl border border-white/10 bg-black/30 px-4 py-2.5 text-sm text-white focus:border-emerald-500/50 focus:outline-none"
            >
              {POSITIONS.map((p) => (
                <option key={p} value={p} className="bg-slate-900">
                  {p}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-medium text-slate-400">Giải đấu</label>
            <select
              value={filters.league}
              onChange={(e) => set('league', e.target.value)}
              className="w-full rounded-xl border border-white/10 bg-black/30 px-4 py-2.5 text-sm text-white focus:border-emerald-500/50 focus:outline-none"
            >
              {LEAGUES.map((l) => (
                <option key={l} value={l} className="bg-slate-900">
                  {l}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="flex flex-col justify-end">
            <label className="mb-1.5 block text-xs font-medium text-slate-400">
              Ngân sách tối đa: {formatCurrency(filters.maxBudget)}
            </label>
            <input
              type="range"
              min={1_000_000}
              max={200_000_000}
              step={1_000_000}
              value={filters.maxBudget}
              onChange={(e) => set('maxBudget', Number(e.target.value))}
              className="w-full accent-emerald-500"
            />
          </div>

          <div className="flex flex-col justify-end">
            <label className="mb-1.5 block text-xs font-medium text-slate-400">
              Độ tuổi: {filters.minAge} – {filters.maxAge}
            </label>
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <span className="w-8 shrink-0 text-xs text-slate-500">Từ</span>
                <input
                  type="range"
                  min={16}
                  max={40}
                  value={filters.minAge}
                  onChange={(e) => set('minAge', Math.min(Number(e.target.value), filters.maxAge - 1))}
                  className="min-w-0 flex-1 accent-emerald-500"
                />
                <span className="w-6 shrink-0 text-right text-xs tabular-nums text-slate-400">{filters.minAge}</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="w-8 shrink-0 text-xs text-slate-500">Đến</span>
                <input
                  type="range"
                  min={17}
                  max={45}
                  value={filters.maxAge}
                  onChange={(e) => set('maxAge', Math.max(Number(e.target.value), filters.minAge + 1))}
                  className="min-w-0 flex-1 accent-emerald-500"
                />
                <span className="w-6 shrink-0 text-right text-xs tabular-nums text-slate-400">{filters.maxAge}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
