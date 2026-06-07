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
  retention: {
    daily_trend: DailyPoint[]
  }
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

function MiniBarChart({ data }: { data: DailyPoint[] }) {
  if (!data || data.length === 0) return (
    <p className="text-xs text-zinc-400 text-center py-6">No trend data yet.</p>
  )
  const max = Math.max(...data.map(d => d.queries), 1)
  return (
    <div className="flex items-end gap-1 h-16 w-full">
      {data.map((d) => {
        const pct = d.queries / max
        const date = new Date(d.date)
        const label = date.toLocaleDateString("en-CA", { month: "short", day: "numeric" })
        return (
          <div key={d.date} className="flex-1 flex flex-col items-center gap-1 group relative">
            <div className="absolute -top-7 left-1/2 -translate-x-1/2 bg-zinc-900 text-white text-[10px] rounded px-1.5 py-0.5 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
              {label}: {d.queries}
            </div>
            <div
              className="w-full rounded-sm bg-zinc-900 transition-all duration-300"
              style={{ height: `${Math.max(pct * 100, 4)}%` }}
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
  const trend = data.retention?.daily_trend ?? []

  // Headline insight
  const headlineAccuracy = s.accuracy !== null ? `${s.accuracy}% of answers rated helpful` : null
  const headlineParts = [
    `${s.total_questions.toLocaleString()} questions asked`,
    headlineAccuracy,
    s.top_department !== "—" ? `most from ${s.top_department}` : null,
  ].filter(Boolean).join(" · ")

  return (
    <div className="min-h-screen bg-[#F7F5F0] text-zinc-900">
      <div className="max-w-4xl mx-auto px-5 py-10">

        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-xl font-bold tracking-tight">CampusQ — Advisor Dashboard</h1>
            <p className="text-sm text-zinc-500 mt-0.5">Anonymized · aggregated student data</p>
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

        {/* Headline insight */}
        <div className="bg-zinc-900 text-white rounded-2xl px-6 py-5 mb-6">
          <p className="text-xs font-semibold uppercase tracking-widest text-zinc-400 mb-1">Summary</p>
          <p className="text-base font-medium leading-snug">{headlineParts || "No data yet for this period."}</p>
        </div>

        {/* Stat cards */}
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-3 mb-6">
          {[
            { label: "Questions asked", value: s.total_questions.toLocaleString(), sub: selectedDays === 0 ? "all time" : `last ${selectedDays === 1 ? "24 hours" : `${selectedDays} days`}` },
            { label: "Helpfulness rate", value: s.accuracy !== null ? `${s.accuracy}%` : "—", sub: s.accuracy !== null ? `${s.thumbs_up} up · ${s.thumbs_down} down` : "no ratings yet" },
            { label: "Top department", value: s.top_department, sub: "by question volume" },
          ].map((st) => (
            <div key={st.label} className="bg-white border border-zinc-200 rounded-2xl p-5">
              <p className="text-[11px] font-medium uppercase tracking-wider text-zinc-400 mb-2">{st.label}</p>
              <p className="text-2xl font-bold text-zinc-900 leading-none truncate">{st.value}</p>
              <p className="text-xs text-zinc-400 mt-1.5">{st.sub}</p>
            </div>
          ))}
        </div>

        {/* Daily trend graph */}
        {trend.length > 0 && (
          <div className="bg-white border border-zinc-200 rounded-2xl p-5 mb-6">
            <p className="text-xs font-semibold uppercase tracking-widest text-zinc-400 mb-4">Daily activity</p>
            <MiniBarChart data={trend} />
            <div className="flex justify-between mt-2">
              <span className="text-[10px] text-zinc-300">{trend[0]?.date}</span>
              <span className="text-[10px] text-zinc-300">{trend[trend.length - 1]?.date}</span>
            </div>
          </div>
        )}

        {/* Top 5 questions */}
        {data.top_questions?.length > 0 && (
          <>
            <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-400 mb-3">Top questions from students</h2>
            <div className="bg-white border border-zinc-200 rounded-2xl overflow-hidden mb-6">
              {data.top_questions.map((q, i) => (
                <div key={i} className={`flex items-start gap-3 px-5 py-3.5 ${i < data.top_questions.length - 1 ? "border-b border-zinc-100" : ""}`}>
                  <MessageSquare className="size-3.5 text-zinc-300 mt-0.5 shrink-0" />
                  <p className="flex-1 text-sm text-zinc-700 leading-snug">"{q.question}"</p>
                  {q.count > 1 && (
                    <span className="text-xs text-zinc-400 shrink-0">×{q.count}</span>
                  )}
                </div>
              ))}
            </div>
          </>
        )}

        {/* What students are asking by category */}
        <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-400 mb-3">Questions by category</h2>
        <div className="bg-white border border-zinc-200 rounded-2xl overflow-hidden mb-6">
          {data.intents.length === 0 ? (
            <p className="text-sm text-zinc-400 p-6 text-center">No questions logged for this period.</p>
          ) : data.intents.map((r, i) => (
            <div key={r.intent} className={`flex items-center gap-4 px-5 py-3.5 ${i < data.intents.length - 1 ? "border-b border-zinc-100" : ""}`}>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-zinc-900">{r.label}</span>
                  <Trend t={r.trend} />
                </div>
                {r.example && <p className="text-xs text-zinc-400 truncate mt-0.5">e.g. "{r.example}"</p>}
              </div>
              <span className="text-lg font-bold text-zinc-900 tabular-nums shrink-0">{r.count}</span>
            </div>
          ))}
        </div>

        {/* Where CampusQ is failing */}
        <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-400 mb-3">Where CampusQ is failing</h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 mb-10">
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
