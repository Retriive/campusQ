import type { ChatSession } from "@/components/campus-q/sidebar"
import type { Message } from "@/components/campus-q/chat/types"
import { API_BASE_URL } from "@/lib/api"

export const LOCAL_SESSIONS_KEY = "campusq-sessions"
export const MAX_SYNCED_SESSIONS = 20

export interface ChatCloudPayload {
  sessions: ChatSession[]
  messagesBySession: Record<string, Message[]>
  updatedAt: number
}

function messagesKey(id: string) {
  return `campusq-msgs-${id}`
}

export function readLocalChatPayload(): ChatCloudPayload {
  let sessions: ChatSession[] = []
  try {
    sessions = JSON.parse(localStorage.getItem(LOCAL_SESSIONS_KEY) || "[]")
    if (!Array.isArray(sessions)) sessions = []
  } catch {
    sessions = []
  }

  const messagesBySession: Record<string, Message[]> = {}
  for (const session of sessions.slice(0, MAX_SYNCED_SESSIONS)) {
    try {
      const msgs = JSON.parse(localStorage.getItem(messagesKey(session.id)) || "[]")
      if (Array.isArray(msgs)) messagesBySession[session.id] = msgs
    } catch {
      messagesBySession[session.id] = []
    }
  }

  return {
    sessions: sessions.slice(0, MAX_SYNCED_SESSIONS),
    messagesBySession,
    updatedAt: Math.max(0, ...sessions.map((s) => s.createdAt || 0)),
  }
}

export function writeLocalChatPayload(payload: ChatCloudPayload) {
  const sessions = (payload.sessions || []).slice(0, MAX_SYNCED_SESSIONS)
  localStorage.setItem(LOCAL_SESSIONS_KEY, JSON.stringify(sessions))

  const keep = new Set(sessions.map((s) => s.id))
  for (const [id, msgs] of Object.entries(payload.messagesBySession || {})) {
    if (!keep.has(id)) continue
    localStorage.setItem(messagesKey(id), JSON.stringify(msgs || []))
  }

  // Drop orphaned message bags for sessions no longer in the list.
  try {
    for (let i = localStorage.length - 1; i >= 0; i--) {
      const key = localStorage.key(i)
      if (!key?.startsWith("campusq-msgs-")) continue
      const id = key.slice("campusq-msgs-".length)
      if (!keep.has(id)) localStorage.removeItem(key)
    }
  } catch {}
}

/** Prefer newer session by createdAt; union session lists up to the cap. */
export function mergeChatPayloads(a: ChatCloudPayload, b: ChatCloudPayload): ChatCloudPayload {
  const byId = new Map<string, ChatSession>()
  for (const s of [...(a.sessions || []), ...(b.sessions || [])]) {
    if (!s?.id) continue
    const prev = byId.get(s.id)
    if (!prev || (s.createdAt || 0) >= (prev.createdAt || 0)) {
      byId.set(s.id, s)
    }
  }

  const sessions = [...byId.values()]
    .sort((x, y) => (y.createdAt || 0) - (x.createdAt || 0))
    .slice(0, MAX_SYNCED_SESSIONS)

  const messagesBySession: Record<string, Message[]> = {}
  for (const session of sessions) {
    const left = a.messagesBySession?.[session.id]
    const right = b.messagesBySession?.[session.id]
    // Prefer the longer transcript; if equal length, prefer cloud (b) when b.updatedAt is newer.
    if ((left?.length || 0) > (right?.length || 0)) {
      messagesBySession[session.id] = left || []
    } else if ((right?.length || 0) > 0) {
      messagesBySession[session.id] = right || []
    } else {
      messagesBySession[session.id] = left || []
    }
  }

  return {
    sessions,
    messagesBySession,
    updatedAt: Math.max(a.updatedAt || 0, b.updatedAt || 0, Date.now()),
  }
}

async function authHeaders(getToken: () => Promise<string | null>): Promise<HeadersInit> {
  const token = await getToken().catch(() => null)
  return token ? { Authorization: `Bearer ${token}`, "Content-Type": "application/json" } : { "Content-Type": "application/json" }
}

export async function fetchCloudChats(
  getToken: () => Promise<string | null>,
): Promise<ChatCloudPayload | null> {
  const headers = await authHeaders(getToken)
  if (!("Authorization" in headers)) return null

  const res = await fetch(`${API_BASE_URL}/api/me/chats`, { headers })
  if (res.status === 401 || res.status === 503) return null
  if (!res.ok) throw new Error(`cloud fetch failed: ${res.status}`)
  const data = await res.json()
  return {
    sessions: Array.isArray(data.sessions) ? data.sessions : [],
    messagesBySession: data.messagesBySession && typeof data.messagesBySession === "object"
      ? data.messagesBySession
      : {},
    updatedAt: Number(data.updatedAt) || 0,
  }
}

export async function pushCloudChats(
  getToken: () => Promise<string | null>,
  payload: ChatCloudPayload,
): Promise<ChatCloudPayload | null> {
  const headers = await authHeaders(getToken)
  if (!("Authorization" in headers)) return null

  const body: ChatCloudPayload = {
    ...payload,
    updatedAt: Date.now(),
  }

  const res = await fetch(`${API_BASE_URL}/api/me/chats`, {
    method: "PUT",
    headers,
    body: JSON.stringify(body),
  })
  if (res.status === 401 || res.status === 503) return null
  if (!res.ok) throw new Error(`cloud push failed: ${res.status}`)
  return res.json()
}

/** Wipe synced cloud chats for the signed-in user. */
export async function deleteCloudChats(
  getToken: () => Promise<string | null>,
): Promise<boolean> {
  const headers = await authHeaders(getToken)
  if (!("Authorization" in headers)) return false

  const res = await fetch(`${API_BASE_URL}/api/me`, {
    method: "DELETE",
    headers,
  })
  if (res.status === 401 || res.status === 503) return false
  if (!res.ok) throw new Error(`cloud delete failed: ${res.status}`)
  return true
}

/** Clear on-device chat sessions and message bags. */
export function clearLocalChatPayload() {
  try {
    const sessionsRaw = localStorage.getItem(LOCAL_SESSIONS_KEY) || "[]"
    const sessions = JSON.parse(sessionsRaw)
    if (Array.isArray(sessions)) {
      for (const session of sessions) {
        if (session?.id) localStorage.removeItem(messagesKey(String(session.id)))
      }
    }
  } catch {}
  try {
    for (let i = localStorage.length - 1; i >= 0; i--) {
      const key = localStorage.key(i)
      if (key?.startsWith("campusq-msgs-")) localStorage.removeItem(key)
    }
  } catch {}
  localStorage.removeItem(LOCAL_SESSIONS_KEY)
}
