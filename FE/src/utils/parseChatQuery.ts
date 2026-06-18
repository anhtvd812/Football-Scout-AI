export interface ParsedChatQuery {
  type: 'valuation' | 'similarity' | 'general'
  targetPlayer?: string
  maxPrice?: number
  maxAge?: number
  position?: string
}

const PLAYER_ALIASES: Record<string, string> = {
  'de bruyne': 'Kevin De Bruyne',
  kdb: 'Kevin De Bruyne',
  rodri: 'Rodri',
  haaland: 'Erling Haaland',
  'xavi simons': 'Xavi Simons',
  simons: 'Xavi Simons',
}

const POSITION_MAP: Record<string, string> = {
  cdm: 'CDM',
  cam: 'CAM',
  'tiền vệ': 'CDM',
  'tiền vệ phòng ngự': 'CDM',
  'tiền đạo': 'FW',
  'hậu vệ': 'DF',
  'thủ môn': 'GK',
}

function parsePrice(text: string): number | undefined {
  const lower = text.toLowerCase()
  const match = lower.match(/(\d+)\s*(củ|cu|triệu|m|million|tr)/)
  if (match) return Number(match[1]) * 1_000_000
  const euroMatch = lower.match(/(\d+)\s*(€|eur|euro)/)
  if (euroMatch) return Number(euroMatch[1]) * 1_000_000
  if (lower.includes('dưới 20') || lower.includes('< 20')) return 20_000_000
  if (lower.includes('dưới 30') || lower.includes('< 30')) return 30_000_000
  return undefined
}

function parseAge(text: string): number | undefined {
  const match = text.match(/(?:dưới|<|≤|<=)\s*(\d{2})\s*(?:tuổi|t)?/i)
  if (match) return Number(match[1])
  return undefined
}

function extractPlayerName(text: string): string | undefined {
  const lower = text.toLowerCase()
  for (const [alias, name] of Object.entries(PLAYER_ALIASES)) {
    if (lower.includes(alias)) return name
  }
  const giốngMatch = text.match(/giống\s+([A-Za-zÀ-ỹ\s\-']+?)(?:\s+giá|\s+dưới|\s*$|,)/i)
  if (giốngMatch) return giốngMatch[1].trim()
  const valuationMatch = text.match(/định giá\s+([A-Za-zÀ-ỹ\s\-']+)/i)
  if (valuationMatch) return valuationMatch[1].trim()
  return undefined
}

export function parseChatMessage(message: string): ParsedChatQuery {
  const lower = message.toLowerCase()
  const maxPrice = parsePrice(message)
  const maxAge = parseAge(message)
  let position: string | undefined

  for (const [key, val] of Object.entries(POSITION_MAP)) {
    if (lower.includes(key)) {
      position = val
      break
    }
  }

  if (lower.includes('định giá') || lower.includes('valuation')) {
    return { type: 'valuation', targetPlayer: extractPlayerName(message), maxPrice, maxAge, position }
  }

  if (lower.includes('giống') || lower.includes('tìm') || lower.includes('similar')) {
    return { type: 'similarity', targetPlayer: extractPlayerName(message), maxPrice, maxAge, position }
  }

  return { type: 'general', maxPrice, maxAge, position }
}
