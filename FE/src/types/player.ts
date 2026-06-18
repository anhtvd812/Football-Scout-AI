export type MarketStatus = 'Undervalued' | 'Fair' | 'Overvalued'

export interface PlayerStats {
  shooting: number
  passing: number
  dribbling: number
  defending: number
  physical: number
  creativity: number
}

export interface SimilarPlayer {
  name: string
  similarity_score: number
  price: number
  position?: string
  age?: number
  league?: string
}

export interface Player {
  id: string
  player_name: string
  position: string
  league: string
  age: number
  nationality: string
  image_url?: string
  actual_market_value_eur: number
  predicted_value_eur: number
  market_status: MarketStatus
  stats: PlayerStats
  similar_players?: SimilarPlayer[]
  compare_with?: {
    name: string
    stats: PlayerStats
  }
}

export interface PlayerFilters {
  search: string
  position: string
  league: string
  minAge: number
  maxAge: number
  maxBudget: number
}

export interface ChatQueryPayload {
  message: string
}

export interface ChatResponse {
  reply: string
  player?: Player
  similar_players?: SimilarPlayer[]
}

export interface ApiPlayerResponse {
  player_name: string
  predicted_value_eur: number
  actual_market_value_eur: number
  market_status: MarketStatus
  similar_players?: SimilarPlayer[]
}
