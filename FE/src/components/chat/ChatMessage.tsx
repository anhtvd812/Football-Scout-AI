import type { ChatResponse } from '../../types/player'
import { formatCurrency } from '../../utils/formatters'
import { MiniPlayerCard } from './MiniPlayerCard'
import { StatusBadge } from '../ui/StatusBadge'

export interface ChatMessageData {
  id: string
  role: 'user' | 'assistant'
  content: string
  response?: ChatResponse
  loading?: boolean
}

export function ChatMessageBubble({ message }: { message: ChatMessageData }) {
  const isUser = message.role === 'user'

  if (message.loading) {
    return (
      <div className="flex justify-start">
        <div className="max-w-[85%] rounded-2xl rounded-bl-md bg-white/5 px-4 py-3">
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <span className="inline-flex gap-1">
              <span className="h-2 w-2 animate-bounce rounded-full bg-emerald-400 [animation-delay:0ms]" />
              <span className="h-2 w-2 animate-bounce rounded-full bg-emerald-400 [animation-delay:150ms]" />
              <span className="h-2 w-2 animate-bounce rounded-full bg-emerald-400 [animation-delay:300ms]" />
            </span>
            AI đang phân tích hàng ngàn dữ liệu...
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[90%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
          isUser
            ? 'rounded-br-md bg-emerald-600 text-white'
            : 'rounded-bl-md bg-white/5 text-slate-200 border border-white/5'
        }`}
      >
        {!isUser && (
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-emerald-500">
            Trợ lý Trinh sát
          </p>
        )}
        <p>{message.content}</p>

        {message.response?.player && (
          <div className="mt-3 rounded-xl border border-white/10 bg-black/30 p-3">
            <div className="flex items-center justify-between gap-2">
              <p className="font-semibold text-white">{message.response.player.player_name}</p>
              <StatusBadge status={message.response.player.market_status} />
            </div>
            <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
              <span className="text-slate-400">
                Thị trường:{' '}
                <strong className="text-white">
                  {formatCurrency(message.response.player.actual_market_value_eur)}
                </strong>
              </span>
              <span className="text-emerald-400">
                AI:{' '}
                <strong>{formatCurrency(message.response.player.predicted_value_eur)}</strong>
              </span>
            </div>
          </div>
        )}

        {message.response?.similar_players?.map((p) => (
          <MiniPlayerCard key={p.name} player={p} />
        ))}
      </div>
    </div>
  )
}
