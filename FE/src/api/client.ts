const API_BASE = import.meta.env.VITE_API_URL ?? ''
const USE_MOCK = !API_BASE || import.meta.env.VITE_USE_MOCK === 'true'

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  })
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    throw new Error(text || `API error ${res.status}`)
  }
  return res.json() as Promise<T>
}

export function isUsingMock(): boolean {
  return USE_MOCK
}

export { fetchJson, API_BASE }
