"use client"

import * as React from "react"
import { ArrowUp, ArrowDown, Minus, RefreshCw, AlertTriangle, ThumbsDown, Loader2, MessageSquare } from "lucide-react"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface IntentRow { intent: string; label: string; count: number; example: string; trend: "up" | "down" | "flat"; prev_count: number }
interface UnansweredGroup { theme: string; count: number; examples: string[] }
interface NegativeItem { question: string; answer: string; department: string }
interface TopQuestion { question: string; count: number }
interface DailyPoint { date: string; queries: number }

const TIMEFRAMES = [
  { label: "Last 24 hours", days: 1   },
  { label: "Last week",     days: 7   },
  { label: "Last 3 months", days: 90  },
  { label: "Last 6 months", days: 180 },
  { label: "Last year",     days: 365 },
  { label: "All time",      days: 0   },
]

interface DashboardData {
  generated_at: string
  days: number | null
  window_start: string
  snapshot: {
    total_questions: number
    accuracy: number | null
    thumbs_up: number
    thumbs_down: number
    top_department: string
  }
  daily_trend: DailyPoint[]
  intents: IntentRow[]
  top_questions: TopQuestion[]
  unanswered: UnansweredGroup[]
  negative_feedback: NegativeItem[]
}

function Trend({ t }: { t: "up" | "down" | "flat" }) {
  if (t === "up")   return <ArrowUp className="size-3 text-emerald-500" />
  if (t === "down") return <ArrowDown className="size-3 text-red-400" />
  return <Minus className="size-3 text-zinc-300" />
}

function BarChart({ data }: { data: DailyPoint[] }) {
  if (!data || data.length === 0) return (
    <div className="flex items-center justify-center h-24 text-xs text-zinc-400">No activity data yet.</div>
  )
  const max = Math.max(...data.map(d => d.queries), 1)
  return (
    <div className="flex items-end gap-[3px] h-24 w-full pt-2">
      {data.map((d) => {
        const pct = d.queries / max
        const date = new Date(d.date + "T12:00:00")
        const label = date.toLocaleDateString("en-CA", { month: "short", day: "numeric" })
        return (
          <div key={d.date} className="flex-1 flex flex-col items-center gap-0.5 group relative">
            <div className="absolute -top-6 left-1/2 -translate-x-1/2 bg-zinc-900 text-white text-[10px] rounded px-1.5 py-0.5 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
              {label}: {d.queries}
            </div>
            <div
              className="w-full rounded-sm bg-zinc-800 hover:bg-zinc-600 transition-colors cursor-default"
              style={{ height: `${Math.max(pct * 100, 6)}%` }}
            />
          </div>
        )
      })}
    </div>
  )
}

export default function DashboardPage() {
  const [data, setData] = React.useState<DashboardData | null>(null)
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState("")
  const [selectedDays, setSelectedDays] = React.useState(7)

  const load = async (days: number = selectedDays) => {
    setLoading(true); setError("")
    try {
      const res = await fetch(`${API_URL}/api/dashboard?days=${days}`)
      const json = await res.json()
      if (!json.ok) { setError("Couldn't load dashboard data."); return }
      setData(json.data)
    } catch {
      setError("Couldn't reach the server. Is the backend running?")
    } finally {
      setLoading(false)
    }
  }

  const handleTimeframe = (days: number) => {
    setSelectedDays(days)
    load(days)
  }

  React.useEffect(() => { load() }, [])

  if (loading && !data) {
    return (
      <div className="min-h-screen bg-[#F7F5F0] flex items-center justify-center">
        <div className="flex items-center gap-2 text-zinc-400 text-sm">
          <Loader2 className="size-4 animate-spin" /> Loading dashboard…
        </div>
      </div>
    )
  }

  if (error && !data) {
    return (
      <div className="min-h-screen bg-[#F7F5F0] flex items-center justify-center px-5">
        <div className="text-center">
          <p className="text-sm text-zinc-600 mb-3">{error}</p>
          <button onClick={() => load(selectedDays)} className="text-sm text-zinc-900 underline underline-offset-2">Retry</button>
        </div>
      </div>
    )
  }

  if (!data) return null
  const s = data.snapshot
  const trend = data.daily_trend ?? []

  const headlineParts = [
    `${s.total_questions.toLocaleString()} questions asked`,
    s.accuracy !== null ? `${s.accuracy}% rated helpful` : null,
    s.top_department !== "—" ? `most from ${s.top_department}` : null,
  ].filter(Boolean).join(" · ")

  const timeLabel = selectedDays === 0 ? "all time" : selectedDays === 1 ? "last 24 hours" : `last ${selectedDays} days`

  return (
    <div className="min-h-screen bg-[#F7F5F0] text-zinc-900">
      <div className="max-w-5xl mx-auto px-5 py-10">

        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-xl font-bold tracking-tight">CampusQ — Advisor Dashboard</h1>
            <p className="text-sm text-zinc-500 mt-0.5">Anonymized · aggregated student data · {timeLabel}</p>
          </div>
          <div className="flex items-center gap-2">
            <div className="relative">
              <select
                value={selectedDays}
                onChange={(e) => handleTimeframe(Number(e.target.value))}
                className="appearance-none bg-white border border-zinc-200 rounded-lg px-3 py-1.5 pr-8 text-sm text-zinc-700 font-medium shadow-sm hover:border-zinc-300 focus:outline-none focus:ring-2 focus:ring-zinc-200 cursor-pointer transition-colors"
              >
                {TIMEFRAMES.map((tf) => (
                  <option key={tf.days} value={tf.days}>{tf.label}</option>
                ))}
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-2 flex items-center">
                <svg className="size-3.5 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
            <button
              onClick={() => load(selectedDays)}
              className="inline-flex items-center gap-1.5 text-sm text-zinc-500 hover:text-zinc-900 bg-white border border-zinc-200 rounded-lg px-3 py-1.5 shadow-sm hover:border-zinc-300 transition-colors"
            >
              <RefreshCw className={`size-3.5 ${loading ? "animate-spin" : ""}`} /> Refresh
            </button>
          </div>
        </div>

        {/* Headline */}
        <div className="bg-zinc-900 text-white rounded-2xl px-6 py-5 mb-6">
          <p className="text-[11px] font-semibold uppercase tracking-widest text-zinc-500 mb-1">Summary</p>
          <p className="text-base font-medium leading-snug">{headlineParts || "No data yet for this period."}</p>
        </div>

        {/* Row: Stats + Chart side by side */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">

          {/* Left: stat cards stacked */}
          <div className="flex flex-col gap-3">
            {[
              {
                label: "Questions asked",
                value: s.total_questions.toLocaleString(),
                sub: timeLabel,
              },
              {
                label: "Helpfulness rate",
                value: s.accuracy !== null ? `${s.accuracy}%` : "—",
                sub: s.accuracy !== null ? `${s.thumbs_up} 👍  ${s.thumbs_down} 👎` : "no ratings yet",
              },
              {
                label: "Top department",
                value: s.top_department,
                sub: "by question volume",
              },
            ].map((st) => (
              <div key={st.label} className="bg-white border border-zinc-200 rounded-2xl px-5 py-4 flex items-center justify-between">
                <div>
                  <p className="text-[11px] font-medium uppercase tracking-wider text-zinc-400">{st.label}</p>
                  <p className="text-xs text-zinc-400 mt-0.5">{st.sub}</p>
                </div>
                <p className="text-2xl font-bold text-zinc-900 tabular-nums">{st.value}</p>
              </div>
            ))}
          </div>

          {/* Right: bar chart */}
          <div className="bg-white border border-zinc-200 rounded-2xl p-5 flex flex-col justify-between">
            <p className="text-[11px] font-semibold uppercase tracking-widest text-zinc-400 mb-3">Daily activity</p>
            <BarChart data={trend} />
            {trend.length > 0 && (
              <div className="flex justify-between mt-2">
                <span className="text-[10px] text-zinc-300">{new Date(trend[0].date + "T12:00:00").toLocaleDateString("en-CA", { month: "short", day: "numeric" })}</span>
                <span className="text-[10px] text-zinc-300">{new Date(trend[trend.length - 1].date + "T12:00:00").toLocaleDateString("en-CA", { month: "short", day: "numeric" })}</span>
              </div>
            )}
          </div>
        </div>

        {/* Row: Top questions + Categories side by side */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">

          {/* Top 5 questions */}
          {data.top_questions?.length > 0 && (
            <div className="bg-white border border-zinc-200 rounded-2xl overflow-hidden">
              <div className="px-5 pt-5 pb-3">
                <p className="text-[11px] font-semibold uppercase tracking-widest text-zinc-400">Top questions</p>
              </div>
              {data.top_questions.map((q, i) => (
                <div key={i} className={`flex items-start gap-3 px-5 py-3 ${i < data.top_questions.length - 1 ? "border-b border-zinc-100" : ""}`}>
                  <MessageSquare className="size-3.5 text-zinc-300 mt-0.5 shrink-0" />
                  <p className="flex-1 text-sm text-zinc-700 leading-snug line-clamp-2">"{q.question}"</p>
                  {q.count > 1 && <span className="text-xs text-zinc-400 shrink-0 tabular-nums">×{q.count}</span>}
                </div>
              ))}
            </div>
          )}

          {/* Categories */}
          <div className="bg-white border border-zinc-200 rounded-2xl overflow-hidden">
            <div className="px-5 pt-5 pb-3">
              <p className="text-[11px] font-semibold uppercase tracking-widest text-zinc-400">Questions by category</p>
            </div>
            {data.intents.length === 0 ? (
              <p className="text-sm text-zinc-400 px-5 pb-5">No questions logged for this period.</p>
            ) : data.intents.map((r, i) => (
              <div key={r.intent} className={`flex items-center gap-3 px-5 py-3 ${i < data.intents.length - 1 ? "border-b border-zinc-100" : ""}`}>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="text-sm font-medium text-zinc-900">{r.label}</span>
                    <Trend t={r.trend} />
                  </div>
                  {r.example && <p className="text-xs text-zinc-400 truncate mt-0.5">"{r.example}"</p>}
                </div>
                <span className="text-base font-bold text-zinc-900 tabular-nums shrink-0">{r.count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Failing section */}
        <p className="text-[11px] font-semibold uppercase tracking-widest text-zinc-400 mb-3">Where CampusQ is failing</p>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-10">
          <div className="bg-white border border-zinc-200 rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle className="size-3.5 text-amber-500" />
              <p className="text-sm font-semibold text-zinc-900">Unanswered questions</p>
            </div>
            {data.unanswered.length === 0 ? (
              <p className="text-xs text-zinc-400">No gaps — every question found an answer.</p>
            ) : (
              <div className="space-y-3">
                {data.unanswered.map((g) => (
                  <div key={g.theme}>
                    <p className="text-xs font-medium text-zinc-700">{g.theme} <span className="text-zinc-400">({g.count})</span></p>
                    {g.examples.map((ex, j) => (
                      <p key={j} className="text-xs text-zinc-400 truncate pl-2 mt-0.5">· {ex}</p>
                    ))}
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="bg-white border border-zinc-200 rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-3">
              <ThumbsDown className="size-3.5 text-red-400" />
              <p className="text-sm font-semibold text-zinc-900">Thumbs-down answers</p>
            </div>
            {data.negative_feedback.length === 0 ? (
              <p className="text-xs text-zinc-400">No negative feedback this period.</p>
            ) : (
              <div className="space-y-3">
                {data.negative_feedback.map((n, i) => (
                  <div key={i} className="border-l-2 border-red-200 pl-3">
                    <p className="text-xs font-medium text-zinc-700">{n.question}</p>
                    <p className="text-xs text-zinc-400 mt-0.5 line-clamp-2">{n.answer}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <p className="text-xs text-zinc-400 text-center pb-6">
          All data is aggregated and anonymized. No student names, IDs, or individual tracking.
        </p>
      </div>
    </div>
  )
}
