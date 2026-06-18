import type { PlayerStats } from '../../types/player'

const LABELS: { key: keyof PlayerStats; label: string }[] = [
  { key: 'shooting', label: 'Dứt điểm' },
  { key: 'passing', label: 'Chuyền bóng' },
  { key: 'dribbling', label: 'Kỹ thuật' },
  { key: 'defending', label: 'Phòng ngự' },
  { key: 'physical', label: 'Thể lực' },
  { key: 'creativity', label: 'Sáng tạo' },
]

interface RadarChartProps {
  playerStats: PlayerStats
  compareStats?: PlayerStats
  playerName: string
  compareName?: string
}

export function RadarChart({ playerStats, compareStats, playerName, compareName }: RadarChartProps) {
  const size = 280
  const center = size / 2
  const maxR = center - 40
  const count = LABELS.length

  const point = (value: number, index: number, r = maxR) => {
    const angle = (Math.PI * 2 * index) / count - Math.PI / 2
    const dist = (value / 100) * r
    return { x: center + dist * Math.cos(angle), y: center + dist * Math.sin(angle) }
  }

  const polygon = (stats: PlayerStats) =>
    LABELS.map(({ key }, i) => {
      const p = point(stats[key], i)
      return `${p.x},${p.y}`
    }).join(' ')

  const gridLevels = [25, 50, 75, 100]

  return (
    <div className="flex flex-col items-center">
      <svg viewBox={`0 0 ${size} ${size}`} className="w-full max-w-[320px]">
        {gridLevels.map((level) => (
          <polygon
            key={level}
            points={LABELS.map((_, i) => {
              const p = point(level, i)
              return `${p.x},${p.y}`
            }).join(' ')}
            fill="none"
            stroke="rgba(255,255,255,0.08)"
            strokeWidth="1"
          />
        ))}

        {LABELS.map(({ label }, i) => {
          const p = point(100, i, maxR + 24)
          const axis = point(100, i)
          return (
            <g key={label}>
              <line x1={center} y1={center} x2={axis.x} y2={axis.y} stroke="rgba(255,255,255,0.06)" />
              <text
                x={p.x}
                y={p.y}
                textAnchor="middle"
                dominantBaseline="middle"
                className="fill-slate-400 text-[10px] font-medium"
              >
                {label}
              </text>
            </g>
          )
        })}

        {compareStats && (
          <polygon
            points={polygon(compareStats)}
            fill="rgba(251,191,36,0.12)"
            stroke="rgb(251,191,36)"
            strokeWidth="2"
            strokeDasharray="4 2"
          />
        )}

        <polygon
          points={polygon(playerStats)}
          fill="rgba(16,185,129,0.2)"
          stroke="rgb(16,185,129)"
          strokeWidth="2"
        />

        {LABELS.map(({ key }, i) => {
          const p = point(playerStats[key], i)
          return <circle key={key} cx={p.x} cy={p.y} r="4" fill="rgb(16,185,129)" />
        })}
      </svg>

      <div className="mt-2 flex flex-wrap justify-center gap-4 text-xs">
        <span className="flex items-center gap-1.5 text-emerald-400">
          <span className="h-2.5 w-2.5 rounded-full bg-emerald-400" />
          {playerName}
        </span>
        {compareStats && compareName && (
          <span className="flex items-center gap-1.5 text-amber-400">
            <span className="h-2.5 w-2.5 rounded-full border border-amber-400 border-dashed bg-amber-400/30" />
            {compareName}
          </span>
        )}
      </div>
    </div>
  )
}
