"use client"

import * as React from "react"
import { ArrowUp, ArrowDown, Minus, RefreshCw, AlertTriangle, ThumbsDown, Loader2, MessageSquare, Mail } from "lucide-react"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface IntentRow { intent: string; label: string; count: number; example: string; trend: "up" | "down" | "flat"; prev_count: number }
interface UnansweredGroup { theme: string; count: number; examples: string[] }
interface NegativeItem { question: string; answer: string; department: string }
interface TopQuestion { question: string; count: number }
interface HourlyPoint { hour: number; queries: number }
interface WaitlistSchoolRow { school: string; count: number }
interface WaitlistRecent { email: string; school: string; ts: string }
interface WaitlistData { total: number; by_school: WaitlistSchoolRow[]; recent: WaitlistRecent[] }

const TIMEFRAMES = [
  { label: "24h",      days: 1   },
  { label: "7d",       days: 7   },
  { label: "30d",      days: 30  },
  { label: "90d",      days: 90  },
  { label: "All time", days: 0   },
]

interface DashboardData {
  snapshot: {
    total_questions: number
    accuracy: number | null
    thumbs_up: number
    thumbs_down: number
    top_department: string
  }
  hourly_trend: HourlyPoint[]
  intents: IntentRow[]
  top_questions: TopQuestion[]
  unanswered: UnansweredGroup[]
  negative_feedback: NegativeItem[]
}

function Trend({ t }: { t: "up" | "down" | "flat" }) {
  if (t === "up")   return <ArrowUp className="size-3 text-emerald-500" />
  if (t === "down") return <ArrowDown className="size-3 text-rose-400" />
  return <Minus className="size-3 text-stone-300" />
}

function formatHour(h: number) {
  if (h === 0)  return "12a"
  if (h < 12)   return `${h}a`
  if (h === 12) return "12p"
  return `${h - 12}p`
}

function HourlyChart({ data }: { data: HourlyPoint[] }) {
  if (!data || data.length === 0) return (
    <div className="flex items-center justify-center h-full text-xs text-stone-400">No data yet.</div>
  )
  const max = Math.max(...data.map(d => d.queries), 1)

  // Color bars by time of day — warm gold for day, deep indigo for night
  const barColor = (h: number) => {
    if (h >= 5 && h < 9)   return "bg-amber-300"   // early morning
    if (h >= 9 && h < 17)  return "bg-amber-400"   // office hours
    if (h >= 17 && h < 21) return "bg-orange-400"  // evening
    return "bg-indigo-400"                          // late night / overnight
  }

  // Only show every 3rd label to avoid crowding
  const showLabel = (h: number) => h % 3 === 0

  return (
    <div className="flex flex-col h-full w-full">
      <div className="flex items-end gap-0.5 flex-1 w-full min-h-0">
        {data.map((d) => (
          <div key={d.hour} className="flex-1 flex flex-col items-center gap-0.5 group relative h-full justify-end">
            {d.queries > 0 && (
              <div className="absolute -top-7 left-1/2 -translate-x-1/2 bg-stone-800 text-white text-[10px] rounded-md px-2 py-0.5 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                {formatHour(d.hour)}: {d.queries}
              </div>
            )}
            <div
              className={`w-full rounded-t-sm ${barColor(d.hour)} transition-all cursor-default ${d.queries === 0 ? "opacity-20" : "opacity-90 hover:opacity-100"}`}
              style={{ height: `${Math.max((d.queries / max) * 100, d.queries > 0 ? 4 : 2)}px` }}
            />
          </div>
        ))}
      </div>
      {/* X axis labels */}
      <div className="flex mt-2">
        {data.map((d) => (
          <div key={d.hour} className="flex-1 text-center">
            {showLabel(d.hour) && (
              <span className="text-[11px] text-stone-500 font-medium">{formatHour(d.hour)}</span>
            )}
          </div>
        ))}
      </div>
      {/* Legend */}
      <div className="flex items-center gap-4 mt-2.5 flex-wrap">
        {[
          { color: "bg-amber-300", label: "Early morning" },
          { color: "bg-amber-400", label: "Office hours" },
          { color: "bg-orange-400", label: "Evening" },
          { color: "bg-indigo-400", label: "Late night" },
        ].map((l) => (
          <div key={l.label} className="flex items-center gap-1.5">
            <div className={`size-2 rounded-sm ${l.color}`} />
            <span className="text-[11px] text-stone-500">{l.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const [data, setData] = React.useState<DashboardData | null>(null)
  const [waitlist, setWaitlist] = React.useState<WaitlistData | null>(null)
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState("")
  const [selectedDays, setSelectedDays] = React.useState(7)

  const load = async (days: number = selectedDays) => {
    setLoading(true); setError("")
    try {
      const [res, wres] = await Promise.all([
        fetch(`${API_URL}/api/dashboard?days=${days}`),
        fetch(`${API_URL}/api/dashboard/waitlist?days=0`),
      ])
      const json = await res.json()
      if (!json.ok) { setError("Couldn't load dashboard data."); return }
      setData(json.data)
      const wjson = await wres.json()
      if (wjson.ok) setWaitlist(wjson.data)
    } catch {
      setError("Couldn't reach the server.")
    } finally {
      setLoading(false)
    }
  }

  const handleTimeframe = (days: number) => {
    setSelectedDays(days)
    load(days)
  }

  React.useEffect(() => { load() }, [])

  if (loading && !data) return (
    <div className="h-screen bg-[#F5F0E8] flex items-center justify-center">
      <Loader2 className="size-5 animate-spin text-stone-300" />
    </div>
  )

  if (error && !data) return (
    <div className="h-screen bg-[#F5F0E8] flex items-center justify-center">
      <div className="text-center space-y-2">
        <p className="text-sm text-stone-400">{error}</p>
        <button onClick={() => load(selectedDays)} className="text-xs text-stone-700 underline">Retry</button>
      </div>
    </div>
  )

  if (!data) return null
  const s = data.snapshot
  const timeLabel = selectedDays === 0 ? "all time" : selectedDays === 1 ? "last 24h" : `last ${selectedDays}d`

  return (
    <div className="h-screen bg-[#F5F0E8] text-stone-900 flex flex-col overflow-hidden">

      {/* Header */}
      <header className="shrink-0 flex items-center justify-between px-8 h-14 bg-[#F5F0E8] border-b border-stone-200">
        <div className="flex items-center gap-2.5">
          <span className="text-sm font-bold tracking-tight text-stone-800">CampusQ</span>
          <span className="text-stone-300">·</span>
          <span className="text-sm text-stone-500">Advisor Dashboard</span>
        </div>
        <div className="flex items-center gap-1 bg-stone-200/60 rounded-xl p-1">
          {TIMEFRAMES.map((tf) => (
            <button
              key={tf.days}
              onClick={() => handleTimeframe(tf.days)}
              className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                selectedDays === tf.days
                  ? "bg-white text-stone-900 shadow-sm"
                  : "text-stone-400 hover:text-stone-700"
              }`}
            >
              {tf.label}
            </button>
          ))}
          <div className="w-px h-4 bg-stone-300 mx-1" />
          <button
            onClick={() => load(selectedDays)}
            className="p-1.5 rounded-lg text-stone-400 hover:text-stone-700 hover:bg-white/60 transition-all"
          >
            <RefreshCw className={`size-3.5 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </header>

      {/* Grid */}
      <div className="flex-1 min-h-0 p-5 grid grid-cols-12 grid-rows-2 gap-4">

        {/* ── Top row ── */}

        {/* 3 stat cards stacked in one column */}
        <div className="col-span-2 flex flex-col gap-2">
          <div className="flex-1 bg-white rounded-2xl px-4 py-3 flex items-center justify-between shadow-sm border border-stone-100">
            <p className="text-xs text-stone-400">Questions asked</p>
            <div className="text-right">
              <p className="text-xl font-bold text-stone-900 tabular-nums">{s.total_questions.toLocaleString()}</p>
              <p className="text-[10px] text-stone-400">{timeLabel}</p>
            </div>
          </div>
          <div className="flex-1 bg-white rounded-2xl px-4 py-3 flex items-center justify-between shadow-sm border border-stone-100">
            <p className="text-xs text-stone-400">Helpfulness</p>
            <div className="text-right">
              <p className="text-xl font-bold text-emerald-600 tabular-nums">{s.accuracy !== null ? `${s.accuracy}%` : "—"}</p>
              <p className="text-[10px] text-stone-400">{s.accuracy !== null ? `${s.thumbs_up} 👍 · ${s.thumbs_down} 👎` : "no ratings yet"}</p>
            </div>
          </div>
          <div className="flex-1 bg-white rounded-2xl px-4 py-3 flex items-center justify-between shadow-sm border border-stone-100">
            <p className="text-xs text-stone-400">Top dept.</p>
            <div className="text-right">
              <p className="text-sm font-bold text-stone-900 leading-tight">{s.top_department}</p>
              <p className="text-[10px] text-stone-400">by volume</p>
            </div>
          </div>
        </div>

        {/* Time of day chart */}
        <div className="col-span-8 bg-white rounded-2xl p-5 flex flex-col shadow-sm border border-stone-100">
          <p className="text-xs font-medium text-stone-400 mb-3 shrink-0">When students ask questions</p>
          <div className="flex-1 min-h-0">
            <HourlyChart data={data.hourly_trend ?? []} />
          </div>
        </div>

        {/* Waitlist signups */}
        <div className="col-span-2 bg-white rounded-2xl flex flex-col overflow-hidden shadow-sm border border-stone-100">
          <div className="px-4 pt-4 pb-2 shrink-0 flex items-center gap-2 border-b border-stone-50">
            <Mail className="size-3.5 text-stone-300" />
            <p className="text-xs font-semibold text-stone-500">Waitlist</p>
          </div>
          <div className="px-4 py-2 shrink-0 border-b border-stone-50">
            <p className="text-xl font-bold text-stone-900 tabular-nums">{waitlist?.total ?? 0}</p>
            <p className="text-[10px] text-stone-400">total signups</p>
          </div>
          <div className="flex-1 overflow-y-auto px-4 py-2 space-y-1.5">
            {!waitlist || waitlist.by_school.length === 0 ? (
              <p className="text-xs text-stone-300">No signups yet.</p>
            ) : waitlist.by_school.map((s) => (
              <div key={s.school} className="flex items-center justify-between">
                <span className="text-xs text-stone-600 capitalize truncate">{s.school}</span>
                <span className="text-xs font-semibold text-stone-800 tabular-nums">{s.count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* ── Bottom row ── */}

        {/* Top questions */}
        <div className="col-span-4 bg-white rounded-2xl flex flex-col overflow-hidden shadow-sm border border-stone-100">
          <div className="px-5 pt-5 pb-3 shrink-0 flex items-center gap-2 border-b border-stone-50">
            <MessageSquare className="size-3.5 text-stone-300" />
            <p className="text-xs font-semibold text-stone-500">Top questions</p>
          </div>
          <div className="flex-1 overflow-y-auto divide-y divide-stone-50">
            {!data.top_questions?.length ? (
              <p className="text-xs text-stone-300 px-5 py-3">No data yet.</p>
            ) : data.top_questions.map((q, i) => (
              <div key={i} className="flex items-start gap-3 px-5 py-3 hover:bg-stone-50/50 transition-colors">
                <span className="text-[10px] font-bold text-stone-200 mt-0.5 shrink-0 w-4 tabular-nums">{i + 1}</span>
                <p className="flex-1 text-xs text-stone-600 leading-relaxed line-clamp-2">"{q.question}"</p>
                {q.count > 1 && <span className="text-[10px] text-stone-300 shrink-0 bg-stone-50 px-1.5 py-0.5 rounded-full tabular-nums">×{q.count}</span>}
              </div>
            ))}
          </div>
        </div>

        {/* Category list */}
        <div className="col-span-4 bg-white rounded-2xl flex flex-col overflow-hidden shadow-sm border border-stone-100">
          <div className="px-5 pt-5 pb-3 shrink-0 border-b border-stone-50">
            <p className="text-xs font-semibold text-stone-500">By category</p>
          </div>
          <div className="flex-1 overflow-y-auto divide-y divide-stone-50">
            {data.intents.length === 0 ? (
              <p className="text-xs text-stone-300 px-5 py-3">No data yet.</p>
            ) : data.intents.map((r) => (
              <div key={r.intent} className="flex items-center gap-3 px-5 py-2.5 hover:bg-stone-50/50 transition-colors">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-medium text-stone-700 truncate">{r.label}</span>
                    <Trend t={r.trend} />
                  </div>
                  {r.example && <p className="text-[10px] text-stone-400 truncate mt-0.5">"{r.example}"</p>}
                </div>
                <span className="text-sm font-semibold text-stone-800 tabular-nums shrink-0">{r.count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Needs attention */}
        <div className="col-span-4 bg-white rounded-2xl flex flex-col overflow-hidden shadow-sm border border-stone-100">
          <div className="px-5 pt-5 pb-3 shrink-0 border-b border-stone-50">
            <p className="text-xs font-semibold text-stone-500">Needs attention</p>
          </div>
          <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <AlertTriangle className="size-3 text-amber-400" />
                <p className="text-[10px] font-semibold uppercase tracking-widest text-stone-400">Unanswered</p>
              </div>
              {data.unanswered.length === 0 ? (
                <p className="text-xs text-emerald-600 bg-emerald-50 rounded-xl px-3 py-2">Every question found an answer ✓</p>
              ) : data.unanswered.map((g) => (
                <div key={g.theme} className="mb-2 bg-amber-50 rounded-xl px-3 py-2">
                  <p className="text-xs font-medium text-amber-800">{g.theme} <span className="text-amber-400 font-normal">({g.count})</span></p>
                  {g.examples.slice(0, 2).map((ex, j) => (
                    <p key={j} className="text-[10px] text-amber-600 truncate mt-0.5">· {ex}</p>
                  ))}
                </div>
              ))}
            </div>
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <ThumbsDown className="size-3 text-rose-400" />
                <p className="text-[10px] font-semibold uppercase tracking-widest text-stone-400">Thumbs down</p>
              </div>
              {data.negative_feedback.length === 0 ? (
                <p className="text-xs text-emerald-600 bg-emerald-50 rounded-xl px-3 py-2">No negative feedback ✓</p>
              ) : data.negative_feedback.map((n, i) => (
                <div key={i} className="bg-rose-50 rounded-xl px-3 py-2 mb-2">
                  <p className="text-xs font-medium text-rose-800 line-clamp-1">{n.question}</p>
                  <p className="text-[10px] text-rose-500 line-clamp-2 mt-0.5">{n.answer}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="shrink-0 px-8 py-2 border-t border-stone-200">
        <p className="text-[10px] text-stone-400">All data is aggregated and anonymized · No student names, IDs, or individual tracking</p>
      </div>
    </div>
  )
}
