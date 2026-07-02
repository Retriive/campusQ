"use client"

import * as React from "react"
import { KeyRound } from "lucide-react"

// The internal dashboard endpoints require an X-Admin-Key header
// (backend ADMIN_API_KEY). The key is kept in localStorage on the
// admin's own browser — it is never bundled into the app.
const STORAGE_KEY = "campusq_admin_key"

export function getAdminKey(): string {
  if (typeof window === "undefined") return ""
  try {
    return localStorage.getItem(STORAGE_KEY) || ""
  } catch {
    return ""
  }
}

export function setAdminKey(key: string) {
  try {
    localStorage.setItem(STORAGE_KEY, key)
  } catch {}
}

export function clearAdminKey() {
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch {}
}

export function adminHeaders(): Record<string, string> {
  const key = getAdminKey()
  return key ? { "X-Admin-Key": key } : {}
}

export function AdminKeyGate({ onSubmit, error }: { onSubmit: () => void; error?: string }) {
  const [value, setValue] = React.useState("")

  return (
    <div className="h-screen bg-[#F5F0E8] flex items-center justify-center px-4">
      <form
        onSubmit={(e) => {
          e.preventDefault()
          if (!value.trim()) return
          setAdminKey(value.trim())
          onSubmit()
        }}
        className="w-full max-w-sm bg-white rounded-2xl border border-stone-200 shadow-sm p-6 flex flex-col gap-4"
      >
        <div className="flex items-center gap-2.5">
          <KeyRound className="size-4 text-stone-500" />
          <span className="text-sm font-semibold text-stone-800">Admin access</span>
        </div>
        <p className="text-xs text-stone-500 leading-relaxed">
          This page shows internal data. Enter the admin key (the <code className="font-mono">ADMIN_API_KEY</code> set
          on the backend) to continue.
        </p>
        <input
          type="password"
          autoFocus
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Admin key"
          className="text-sm px-3.5 py-2.5 rounded-xl border border-stone-200 bg-white outline-none focus:border-stone-400 transition-colors font-mono"
        />
        {error && <p className="text-xs text-rose-500">{error}</p>}
        <button
          type="submit"
          className="text-sm font-semibold bg-stone-900 text-white rounded-xl px-4 py-2.5 hover:bg-stone-700 transition-colors"
        >
          Unlock
        </button>
      </form>
    </div>
  )
}
