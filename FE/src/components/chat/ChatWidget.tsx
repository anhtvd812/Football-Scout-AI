import { useCallback, useRef, useState } from 'react'
import { sendChatMessage } from '../../api/players'
import { QUICK_REPLIES } from '../../api/mockData'
import { isUsingMock } from '../../api/client'
import { useToast } from '../ui/Toast'
import { ChatMessageBubble, type ChatMessageData } from './ChatMessage'

export function ChatWidget() {
  const [open, setOpen] = useState(false)
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<ChatMessageData[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        'Xin chào! Tôi là Trợ lý Trinh sát AI. Hỏi tôi về định giá cầu thủ hoặc tìm hidden gem — ví dụ: "Tìm cầu thủ giống De Bruyne giá dưới 20 củ".',
    },
  ])
  const [sending, setSending] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)
  const { toast } = useToast()

  const scrollToBottom = useCallback(() => {
    requestAnimationFrame(() => {
      scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
    })
  }, [])

  const handleSend = async (text: string) => {
    const trimmed = text.trim()
    if (!trimmed || sending) return

    const userMsg: ChatMessageData = { id: `u-${Date.now()}`, role: 'user', content: trimmed }
    const loadingId = `l-${Date.now()}`
    setMessages((prev) => [
      ...prev,
      userMsg,
      { id: loadingId, role: 'assistant', content: '', loading: true },
    ])
    setInput('')
    setSending(true)
    scrollToBottom()

    try {
      const response = await sendChatMessage(trimmed)
      setMessages((prev) =>
        prev
          .filter((m) => m.id !== loadingId)
          .concat({ id: `a-${Date.now()}`, role: 'assistant', content: response.reply, response }),
      )
    } catch {
      setMessages((prev) => prev.filter((m) => m.id !== loadingId))
      toast('Không thể kết nối API. Kiểm tra backend của Hưng hoặc bật mock mode.', 'error')
    } finally {
      setSending(false)
      scrollToBottom()
    }
  }

  return (
    <>
      {/* Floating toggle */}
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="fixed bottom-6 right-6 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-emerald-500 text-2xl shadow-lg shadow-emerald-500/30 transition hover:scale-105 hover:bg-emerald-400"
        aria-label={open ? 'Đóng chat' : 'Mở Trợ lý AI'}
      >
        {open ? '✕' : '🤖'}
      </button>

      {open && (
        <div className="fixed bottom-24 right-6 z-40 flex h-[min(560px,calc(100vh-8rem))] w-[min(400px,calc(100vw-2rem))] flex-col overflow-hidden rounded-2xl border border-white/10 bg-slate-950 shadow-2xl shadow-black/50">
          {/* Header */}
          <div className="border-b border-white/10 bg-gradient-to-r from-emerald-950/80 to-slate-950 px-4 py-3">
            <div className="flex items-center gap-3">
              <span className="flex h-9 w-9 items-center justify-center rounded-full bg-emerald-500/20 text-lg">
                🤖
              </span>
              <div>
                <h3 className="font-semibold text-white">Trợ lý Trinh sát AI</h3>
                <p className="text-[10px] text-emerald-400/80">
                  {isUsingMock() ? 'Demo mode · Mock data' : 'Kết nối API backend'}
                </p>
              </div>
            </div>
          </div>

          {/* Messages */}
          <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.map((m) => (
              <ChatMessageBubble key={m.id} message={m} />
            ))}
          </div>

          {/* Quick replies */}
          <div className="border-t border-white/5 px-3 py-2">
            <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-thin">
              {QUICK_REPLIES.map((q) => (
                <button
                  key={q}
                  type="button"
                  disabled={sending}
                  onClick={() => handleSend(q)}
                  className="shrink-0 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-[11px] font-medium text-emerald-300 transition hover:bg-emerald-500/20 disabled:opacity-50"
                >
                  {q}
                </button>
              ))}
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault()
                handleSend(input)
              }}
              className="flex gap-2"
            >
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Nhập câu hỏi..."
                disabled={sending}
                className="flex-1 rounded-xl border border-white/10 bg-black/40 px-3 py-2.5 text-sm text-white placeholder:text-slate-500 focus:border-emerald-500/50 focus:outline-none disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={sending || !input.trim()}
                className="rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-emerald-950 transition hover:bg-emerald-400 disabled:opacity-50"
              >
                Gửi
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  )
}
