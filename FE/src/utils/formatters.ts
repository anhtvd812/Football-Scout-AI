export function formatCurrency(eur: number): string {
  if (eur >= 1_000_000) {
    const m = eur / 1_000_000
    return m % 1 === 0 ? `€${m}M` : `€${m.toFixed(1)}M`
  }
  return `€${Math.round(eur / 1000)}K`
}

export function formatPercent(score: number): string {
  if (score <= 1) return `${Math.round(score * 100)}%`
  return `${Math.round(score)}%`
}

export function cn(...classes: (string | false | undefined | null)[]): string {
  return classes.filter(Boolean).join(' ')
}
