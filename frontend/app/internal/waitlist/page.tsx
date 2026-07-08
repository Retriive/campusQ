"use client"

import * as React from "react"
import { Mail, RefreshCw, Loader2 } from "lucide-react"
import { AdminKeyGate, adminHeaders, clearAdminKey } from "@/components/admin-key-gate"
import { API_BASE_URL } from "@/lib/api"

interface WaitlistSchoolRow { school: string; count: number }
interface WaitlistRecent { email: string; school: string; ts: string }
interface WaitlistData { total: number; by_school: WaitlistSchoolRow[]; recent: WaitlistRecent[] }

export default function InternalWaitlistPage() {
  const [data, setData] = React.useState<WaitlistData | null>(null)
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState("")
  const [needsKey, setNeedsKey] = React.useState(false)
  const [keyError, setKeyError] = React.useState("")

  const load = async () => {
    setLoading(true); setError("")
    try {
      const res = await fetch(`${API_BASE_URL}/api/dashboard/waitlist?days=0`, { headers: adminHeaders() })
      if (res.status === 401) {
        clearAdminKey()
        setNeedsKey(true)
        setKeyError("That key didn't work — check ADMIN_API_KEY on the backend.")
        return
      }
      if (res.status === 503) {
        setNeedsKey(true)
        setKeyError("The backend has no ADMIN_API_KEY configured yet.")
        return
      }
      const json = await res.json()
      if (!json.ok) { setError("Couldn't load waitlist data."); return }
      setNeedsKey(false)
      setKeyError("")
      setData(json.data)
    } catch {
      setError("Couldn't reach the server.")
    } finally {
      setLoading(false)
    }
  }

  React.useEffect(() => { load() }, [])

  if (needsKey) return <AdminKeyGate onSubmit={load} error={keyError} />

  if (loading && !data) return (
    <div className="h-screen bg-[#F5F0E8] flex items-center justify-center">
      <Loader2 className="size-5 animate-spin text-stone-300" />
    </div>
  )

  if (error && !data) return (
    <div className="h-screen bg-[#F5F0E8] flex items-center justify-center">
      <div className="text-center space-y-2">
        <p className="text-sm text-stone-400">{error}</p>
        <button onClick={load} className="text-xs text-stone-700 underline">Retry</button>
      </div>
    </div>
  )

  if (!data) return null

  return (
    <div className="h-screen bg-[#F5F0E8] text-stone-900 flex flex-col overflow-hidden">

      {/* Header */}
      <header className="shrink-0 flex items-center justify-between px-8 h-14 bg-[#F5F0E8] border-b border-stone-200">
        <div className="flex items-center gap-2.5">
          <Mail className="size-4 text-stone-500" />
          <span className="text-sm font-bold tracking-tight text-stone-800">CampusQ</span>
          <span className="text-stone-300">·</span>
          <span className="text-sm text-stone-500">Waitlist (internal)</span>
        </div>
        <button
          onClick={load}
          className="p-1.5 rounded-lg text-stone-400 hover:text-stone-700 hover:bg-white/60 transition-all"
        >
          <RefreshCw className={`size-3.5 ${loading ? "animate-spin" : ""}`} />
        </button>
      </header>

      {/* Body */}
      <div className="flex-1 min-h-0 p-5 grid grid-cols-3 gap-4">

        {/* Total + by school */}
        <div className="col-span-1 bg-white rounded-2xl flex flex-col overflow-hidden shadow-sm border border-stone-100">
          <div className="px-5 py-4 border-b border-stone-50">
            <p className="text-2xl font-bold text-stone-900 tabular-nums">{data.total}</p>
            <p className="text-xs text-stone-400">total signups, all time</p>
          </div>
          <div className="flex-1 overflow-y-auto px-5 py-3 space-y-2">
            {data.by_school.length === 0 ? (
              <p className="text-xs text-stone-300">No signups yet.</p>
            ) : data.by_school.map((s) => (
              <div key={s.school} className="flex items-center justify-between">
                <span className="text-sm text-stone-600 capitalize">{s.school}</span>
                <span className="text-sm font-semibold text-stone-800 tabular-nums">{s.count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Recent signups */}
        <div className="col-span-2 bg-white rounded-2xl flex flex-col overflow-hidden shadow-sm border border-stone-100">
          <div className="px-5 pt-5 pb-3 shrink-0 border-b border-stone-50">
            <p className="text-xs font-semibold text-stone-500">Recent signups</p>
          </div>
          <div className="flex-1 overflow-y-auto divide-y divide-stone-50">
            {data.recent.length === 0 ? (
              <p className="text-xs text-stone-300 px-5 py-3">No signups yet.</p>
            ) : data.recent.map((r, i) => (
              <div key={i} className="flex items-center justify-between px-5 py-2.5">
                <span className="text-sm text-stone-700">{r.email}</span>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-stone-400 capitalize">{r.school}</span>
                  <span className="text-[10px] text-stone-300 tabular-nums">{r.ts.slice(0, 10)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
