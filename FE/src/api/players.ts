import type { ChatResponse, Player, PlayerFilters } from '../types/player'
import { fetchJson, isUsingMock } from './client'
import { MOCK_PLAYERS } from './mockData'
import { parseChatMessage } from '../utils/parseChatQuery'

function filterPlayers(players: Player[], filters: PlayerFilters): Player[] {
  return players.filter((p) => {
    if (filters.search) {
      const q = filters.search.toLowerCase()
      if (!p.player_name.toLowerCase().includes(q) && !p.league.toLowerCase().includes(q)) {
        return false
      }
    }
    if (filters.position && filters.position !== 'Tất cả' && p.position !== filters.position) {
      return false
    }
    if (filters.league && filters.league !== 'Tất cả' && p.league !== filters.league) {
      return false
    }
    if (p.age < filters.minAge || p.age > filters.maxAge) return false
    if (p.actual_market_value_eur > filters.maxBudget) return false
    return true
  })
}

function delay(ms: number) {
  return new Promise((r) => setTimeout(r, ms))
}

export async function getPlayers(filters: PlayerFilters): Promise<Player[]> {
  if (isUsingMock()) {
    await delay(600)
    return filterPlayers(MOCK_PLAYERS, filters)
  }

  const params = new URLSearchParams()
  if (filters.search) params.set('search', filters.search)
  if (filters.position !== 'Tất cả') params.set('position', filters.position)
  if (filters.league !== 'Tất cả') params.set('league', filters.league)
  params.set('min_age', String(filters.minAge))
  params.set('max_age', String(filters.maxAge))
  params.set('max_budget', String(filters.maxBudget))

  return fetchJson<Player[]>(`/players?${params}`)
}

export async function getPlayerById(id: string): Promise<Player | null> {
  if (isUsingMock()) {
    await delay(400)
    return MOCK_PLAYERS.find((p) => p.id === id) ?? null
  }
  return fetchJson<Player>(`/players/${id}`)
}

export async function sendChatMessage(message: string): Promise<ChatResponse> {
  if (isUsingMock()) {
    await delay(1200)
    return handleMockChat(message)
  }

  return fetchJson<ChatResponse>('/chat/query', {
    method: 'POST',
    body: JSON.stringify({ message }),
  })
}

function handleMockChat(message: string): ChatResponse {
  const parsed = parseChatMessage(message)
  const lower = message.toLowerCase()

  if (parsed.type === 'valuation' && parsed.targetPlayer) {
    const player = MOCK_PLAYERS.find((p) =>
      p.player_name.toLowerCase().includes(parsed.targetPlayer!.toLowerCase()),
    )
    if (!player) {
      return { reply: `Không tìm thấy cầu thủ "${parsed.targetPlayer}". Vui lòng thử tên khác.` }
    }
    const diff = player.predicted_value_eur - player.actual_market_value_eur
    const pct = Math.round((diff / player.actual_market_value_eur) * 100)
    return {
      reply: `${player.player_name}: Giá thị trường ${formatShort(player.actual_market_value_eur)}, AI dự đoán ${formatShort(player.predicted_value_eur)} (${player.market_status === 'Undervalued' ? `+${pct}%` : `${pct}%`}).`,
      player,
    }
  }

  if (parsed.type === 'similarity') {
    const target = MOCK_PLAYERS.find((p) =>
      p.player_name.toLowerCase().includes((parsed.targetPlayer ?? '').toLowerCase()),
    )
    const reference = target ?? MOCK_PLAYERS.find((p) => p.player_name.includes('De Bruyne'))

    let candidates = MOCK_PLAYERS.filter(
      (p) => p.id !== reference?.id && p.similar_players === undefined,
    )

    if (parsed.position) {
      candidates = candidates.filter((p) => p.position === parsed.position)
    }
    if (parsed.maxPrice) {
      candidates = candidates.filter((p) => p.actual_market_value_eur <= parsed.maxPrice!)
    }
    if (parsed.maxAge) {
      candidates = candidates.filter((p) => p.age <= parsed.maxAge!)
    }

    const similar = (reference?.similar_players ?? candidates.slice(0, 3).map((p, i) => ({
      name: p.player_name,
      similarity_score: 0.92 - i * 0.03,
      price: p.actual_market_value_eur,
      position: p.position,
      age: p.age,
      league: p.league,
    }))).filter((s) => !parsed.maxPrice || s.price <= parsed.maxPrice)

    const targetName = parsed.targetPlayer ?? reference?.player_name ?? 'mục tiêu'
    return {
      reply: `Tìm thấy ${similar.length} cầu thủ tương đồng với ${targetName}${parsed.maxPrice ? ` (≤ ${formatShort(parsed.maxPrice)})` : ''}:`,
      similar_players: similar,
    }
  }

  if (lower.includes('undervalued') || lower.includes('món hời')) {
    const gems = MOCK_PLAYERS.filter(
      (p) => p.market_status === 'Undervalued' && p.age <= (parsed.maxAge ?? 25),
    ).slice(0, 4)
    return {
      reply: `Có ${gems.length} cầu thủ đang bị định giá thấp (Undervalued):`,
      similar_players: gems.map((p) => ({
        name: p.player_name,
        similarity_score: Math.round((p.predicted_value_eur / p.actual_market_value_eur - 1) * 100) / 100,
        price: p.actual_market_value_eur,
        position: p.position,
        age: p.age,
        league: p.league,
      })),
    }
  }

  return {
    reply: 'Tôi có thể giúp bạn định giá cầu thủ hoặc tìm hidden gem. Thử: "Định giá Xavi Simons" hoặc "Tìm cầu thủ giống De Bruyne giá dưới 20 củ".',
  }
}

function formatShort(eur: number): string {
  if (eur >= 1_000_000) return `€${(eur / 1_000_000).toFixed(0)}M`
  return `€${(eur / 1_000).toFixed(0)}K`
}
