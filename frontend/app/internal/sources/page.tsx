"use client"

import * as React from "react"
import { Database, RefreshCw, Loader2, Plus, Play } from "lucide-react"
import { AdminKeyGate, adminHeaders, clearAdminKey } from "@/components/admin-key-gate"
import { API_BASE_URL } from "@/lib/api"

interface SourceRow {
  category: string
  url: string
  extractor: string
  follow_links: boolean
  added_by_admin: boolean
  last_crawled: string | null
  last_changed: string | null
  status: string | null
}
interface RunRow {
  id: number
  category: string
  started: string
  finished: string | null
  status: string
  pages_fetched: number
  pages_changed: number
  records: number
  message: string | null
}
interface SourcesData { sources: SourceRow[]; runs: RunRow[]; running: boolean; schools: string[] }

function timeAgo(iso: string | null): string {
  if (!iso) return "never"
  const s = (Date.now() - new Date(iso + "Z").getTime()) / 1000
  if (s < 3600) return `${Math.max(1, Math.round(s / 60))}m ago`
  if (s < 86400) return `${Math.round(s / 3600)}h ago`
  return `${Math.round(s / 86400)}d ago`
}

const RUN_COLORS: Record<string, string> = {
  ok: "text-emerald-700 bg-emerald-50",
  running: "text-amber-700 bg-amber-50",
  failed: "text-rose-700 bg-rose-50",
  dry_run: "text-stone-600 bg-stone-100",
}

export default function InternalSourcesPage() {
  const [data, setData] = React.useState<SourcesData | null>(null)
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState("")
  const [needsKey, setNeedsKey] = React.useState(false)
  const [keyError, setKeyError] = React.useState("")
  const [banner, setBanner] = React.useState("")
  const [newUrl, setNewUrl] = React.useState("")
  const [newCategory, setNewCategory] = React.useState("services")

  const load = async () => {
    setLoading(true); setError("")
    try {
      const res = await fetch(`${API_BASE_URL}/api/admin/ingest/sources?school=carleton`, { headers: adminHeaders() })
      if (res.status === 401) { clearAdminKey(); setNeedsKey(true); setKeyError("That key didn't work."); return }
      if (res.status === 503) { setNeedsKey(true); setKeyError("The backend has no ADMIN_API_KEY configured yet."); return }
      const json = await res.json()
      if (!json.ok) { setError("Couldn't load sources."); return }
      setNeedsKey(false); setKeyError("")
      setData(json)
    } catch {
      setError("Couldn't reach the server.")
    } finally {
      setLoading(false)
    }
  }

  React.useEffect(() => { load() }, [])

  // Poll while a run is in progress so status/run history stay live
  React.useEffect(() => {
    if (!data?.running) return
    const t = setInterval(load, 5000)
    return () => clearInterval(t)
  }, [data?.running])

  const addSource = async (e: React.FormEvent) => {
    e.preventDefault()
    const fd = new FormData()
    fd.append("school", "carleton")
    fd.append("category", newCategory)
    fd.append("url", newUrl.trim())
    const res = await fetch(`${API_BASE_URL}/api/admin/ingest/sources`, { method: "POST", body: fd, headers: adminHeaders() })
    const json = await res.json()
    if (json.ok) { setNewUrl(""); setBanner("Source added — it'll be picked up on the next run."); load() }
    else setBanner(json.error || "Couldn't add source.")
  }

  const triggerRun = async (category?: string) => {
    const fd = new FormData()
    fd.append("school", "carleton")
    if (category) fd.append("category", category)
    const res = await fetch(`${API_BASE_URL}/api/admin/ingest/run`, { method: "POST", body: fd, headers: adminHeaders() })
    const json = await res.json()
    setBanner(json.ok ? json.message : json.error)
    load()
  }

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

  const categories = [...new Set(data.sources.map((s) => s.category))]

  return (
    <div className="min-h-screen bg-[#F5F0E8] text-stone-900 flex flex-col">

      {/* Header */}
      <header className="shrink-0 flex items-center justify-between px-8 h-14 border-b border-stone-200">
        <div className="flex items-center gap-2.5">
          <Database className="size-4 text-stone-500" />
          <span className="text-sm font-bold tracking-tight text-stone-800">CampusQ</span>
          <span className="text-stone-300">·</span>
          <span className="text-sm text-stone-500">Data sources (internal)</span>
          {data.running && (
            <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-full">
              <Loader2 className="size-3 animate-spin" /> ingesting…
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => triggerRun()}
            disabled={data.running}
            className="inline-flex items-center gap-1.5 text-xs font-semibold bg-stone-900 text-white px-3 py-1.5 rounded-lg hover:bg-stone-700 transition-colors disabled:opacity-40"
          >
            <Play className="size-3" /> Re-scrape everything
          </button>
          <button onClick={load} className="p-1.5 rounded-lg text-stone-400 hover:text-stone-700 hover:bg-white/60 transition-all">
            <RefreshCw className={`size-3.5 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </header>

      {banner && (
        <div className="px-8 py-2 text-xs text-stone-600 bg-amber-50 border-b border-amber-100">{banner}</div>
      )}

      <div className="flex-1 p-6 grid grid-cols-1 lg:grid-cols-3 gap-4 max-w-7xl w-full mx-auto">

        {/* Sources by category */}
        <div className="lg:col-span-2 space-y-4">
          {categories.map((cat) => (
            <div key={cat} className="bg-white rounded-2xl border border-stone-200 overflow-hidden">
              <div className="flex items-center justify-between px-5 py-3 border-b border-stone-100">
                <span className="text-xs font-bold uppercase tracking-widest text-stone-500">{cat}</span>
                <button
                  onClick={() => triggerRun(cat)}
                  disabled={data.running}
                  className="text-[11px] font-semibold text-stone-600 hover:text-stone-900 border border-stone-200 rounded-lg px-2.5 py-1 transition-colors disabled:opacity-40"
                >
                  Re-scrape {cat}
                </button>
              </div>
              {data.sources.filter((s) => s.category === cat).map((s) => (
                <div key={s.url} className="px-5 py-3 border-b border-stone-50 last:border-0 flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <p className="text-sm text-stone-800 truncate">{s.url}</p>
                    <p className="text-[11px] text-stone-400 mt-0.5">
                      {s.extractor}{s.follow_links ? " · follows links" : ""}{s.added_by_admin ? " · added via admin" : ""}
                      {" · crawled "}{timeAgo(s.last_crawled)}
                      {s.last_changed ? ` · changed ${timeAgo(s.last_changed)}` : ""}
                    </p>
                  </div>
                  {s.status && (
                    <span className={`shrink-0 text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${
                      s.status === "ok" ? "text-emerald-700 bg-emerald-50" :
                      s.status === "error" ? "text-rose-700 bg-rose-50" : "text-stone-500 bg-stone-100"
                    }`}>{s.status}</span>
                  )}
                </div>
              ))}
            </div>
          ))}

          {/* Add source */}
          <form onSubmit={addSource} className="bg-white rounded-2xl border border-stone-200 p-5 flex flex-col sm:flex-row gap-2">
            <input
              value={newUrl}
              onChange={(e) => setNewUrl(e.target.value)}
              placeholder="https://carleton.ca/…  (page or PDF to index)"
              required
              className="flex-1 text-sm px-3.5 py-2.5 rounded-xl border border-stone-200 outline-none focus:border-stone-400 transition-colors"
            />
            <select
              value={newCategory}
              onChange={(e) => setNewCategory(e.target.value)}
              className="text-sm px-3 py-2.5 rounded-xl border border-stone-200 bg-white"
            >
              {[...new Set([...categories, "services", "regulations", "registrar", "tuition", "dates", "facts"])].map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
            <button type="submit" className="inline-flex items-center justify-center gap-1.5 text-sm font-semibold bg-stone-900 text-white rounded-xl px-4 py-2.5 hover:bg-stone-700 transition-colors">
              <Plus className="size-3.5" /> Add source
            </button>
          </form>
        </div>

        {/* Run history */}
        <div className="bg-white rounded-2xl border border-stone-200 overflow-hidden h-fit">
          <div className="px-5 py-3 border-b border-stone-100">
            <span className="text-xs font-bold uppercase tracking-widest text-stone-500">Recent runs</span>
          </div>
          {data.runs.length === 0 && (
            <p className="px-5 py-6 text-sm text-stone-400">No runs yet — hit "Re-scrape" to start the first one.</p>
          )}
          {data.runs.map((r) => (
            <div key={r.id} className="px-5 py-3 border-b border-stone-50 last:border-0">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-stone-800">{r.category}</span>
                <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${RUN_COLORS[r.status] || "text-stone-500 bg-stone-100"}`}>
                  {r.status}
                </span>
              </div>
              <p className="text-[11px] text-stone-400 mt-1">
                {timeAgo(r.started)} · {r.pages_fetched} pages · {r.pages_changed} changed · {r.records} records
              </p>
              {r.message && <p className="text-[11px] text-stone-500 mt-1 leading-snug">{r.message}</p>}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
