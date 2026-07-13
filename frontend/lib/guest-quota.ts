import { API_BASE_URL } from "@/lib/api"

const GUEST_ID_KEY = "campusq-guest-id"

export interface GuestQuota {
  used: number
  limit: number
  remaining: number
  day?: string
}

export function getOrCreateGuestId(): string {
  try {
    const existing = localStorage.getItem(GUEST_ID_KEY)
    if (existing && /^[A-Za-z0-9_-]{8,64}$/.test(existing)) return existing
    const id = crypto.randomUUID()
    localStorage.setItem(GUEST_ID_KEY, id)
    return id
  } catch {
    return `tmp-${Date.now().toString(36)}`
  }
}

export function guestHeaders(): HeadersInit {
  return { "X-Guest-Id": getOrCreateGuestId() }
}

export async function fetchGuestQuota(): Promise<GuestQuota | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/guest/quota`, {
      headers: guestHeaders(),
    })
    if (!res.ok) return null
    const data = await res.json()
    return {
      used: Number(data.used) || 0,
      limit: Number(data.limit) || 10,
      remaining: Number(data.remaining) || 0,
      day: data.day,
    }
  } catch {
    return null
  }
}

export function isGuestLimitError(status: number, detail: unknown): boolean {
  if (status !== 429) return false
  if (!detail || typeof detail !== "object") return false
  return (detail as { error?: string }).error === "guest_daily_limit"
}
