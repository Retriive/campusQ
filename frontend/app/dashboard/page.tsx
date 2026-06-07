"use client"

import * as React from "react"
import { ArrowUp, ArrowDown, Minus, RefreshCw, AlertTriangle, ThumbsDown, Loader2 } from "lucide-react"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface IntentRow { intent: string; label: string; count: number; example: string; trend: "up" | "down" | "flat"; prev_count: number }
interface UnansweredGroup { theme: string; count: number; examples: string[] }
interface NegativeItem { question: string; answer: string; department: string }
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
  intents: IntentRow[]
  unanswered: UnansweredGroup[]
  negative_feedback: NegativeItem[]
}

function Trend({ t }: { t: "up" | "down" | "flat" }) {
  if (t === "up")   return <ArrowUp className="size-3 text-emerald-600" />
  if (t === "down") return <ArrowDown className="size-3 text-red-500" />
  return <Minus className="size-3 text-zinc-400" />
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
          <button onClick={load} className="text-sm text-zinc-900 underline underline-offset-2">Retry</button>
        </div>
      </div>
    )
  }

  if (!data) return null
  const s = data.snapshot

  const STATS = [
    { label: "Questions this week", value: s.total_questions.toLocaleString(), sub: "across all students" },
    { label: "Helpfulness rate",    value: s.accuracy !== null ? `${s.accuracy}%` : "—", sub: s.accuracy !== null ? `${s.thumbs_up}👍 ${s.thumbs_down}👎` : "no ratings yet" },
    { label: "Top department",      value: s.top_department, sub: "by question volume" },
  ]

  return (
    <div className="min-h-screen bg-[#F7F5F0] text-zinc-900">
      <div className="max-w-4xl mx-auto px-5 py-10">

        {/* Header */}
        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="text-xl font-bold tracking-tight">CampusQ — Advisor Dashboard</h1>
            <p className="text-sm text-zinc-500 mt-0.5">
              Anonymized · {selectedDays === 0 ? "all time" : `last ${selectedDays} days`}
            </p>
          </div>
          <button
            onClick={() => load()}
            className="inline-flex items-center gap-1.5 text-sm text-zinc-500 hover:text-zinc-900 transition-colors mt-1"
          >
            <RefreshCw className={`size-3.5 ${loading ? "animate-spin" : ""}`} /> Refresh
          </button>
        </div>

        {/* Timeframe selector */}
        <div className="flex flex-wrap gap-2 mb-8">
          {TIMEFRAMES.map((tf) => (
            <button
              key={tf.days}
              onClick={() => handleTimeframe(tf.days)}
              className={`px-3.5 py-1.5 rounded-full text-xs font-medium border transition-colors ${
                selectedDays === tf.days
                  ? "bg-zinc-900 text-white border-zinc-900"
                  : "bg-white text-zinc-500 border-zinc-200 hover:border-zinc-400 hover:text-zinc-900"
              }`}
            >
              {tf.label}
            </button>
          ))}
        </div>

        {/* Section 1 — Snapshot */}
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-3 mb-10">
          {STATS.map((st) => (
            <div key={st.label} className="bg-white border border-zinc-200 rounded-2xl p-5">
              <p className="text-[11px] font-medium uppercase tracking-wider text-zinc-400 mb-2">{st.label}</p>
              <p className="text-2xl font-bold text-zinc-900 leading-none truncate">{st.value}</p>
              <p className="text-xs text-zinc-400 mt-1.5">{st.sub}</p>
            </div>
          ))}
        </div>

        {/* Section 2 — What students are asking */}
        <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-400 mb-3">What students are asking</h2>
        <div className="bg-white border border-zinc-200 rounded-2xl overflow-hidden mb-10">
          {data.intents.length === 0 ? (
            <p className="text-sm text-zinc-400 p-6 text-center">No questions logged this week yet.</p>
          ) : data.intents.map((r, i) => (
            <div key={r.intent} className={`flex items-center gap-4 px-5 py-3.5 ${i < data.intents.length - 1 ? "border-b border-zinc-100" : ""}`}>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-zinc-900">{r.label}</span>
                  <Trend t={r.trend} />
                </div>
                {r.example && <p className="text-xs text-zinc-400 truncate mt-0.5">“{r.example}”</p>}
              </div>
              <span className="text-lg font-bold text-zinc-900 tabular-nums shrink-0">{r.count}</span>
            </div>
          ))}
        </div>

        {/* Section 3 — Where CampusQ is failing */}
        <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-400 mb-3">Where CampusQ is failing</h2>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 mb-10">
          {/* Unanswered */}
          <div className="bg-white border border-zinc-200 rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle className="size-3.5 text-amber-500" />
              <p className="text-sm font-semibold text-zinc-900">Unanswered questions</p>
            </div>
            {data.unanswered.length === 0 ? (
              <p className="text-xs text-zinc-400">No gaps this week — every question found an answer.</p>
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

          {/* Negative feedback */}
          <div className="bg-white border border-zinc-200 rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-3">
              <ThumbsDown className="size-3.5 text-red-400" />
              <p className="text-sm font-semibold text-zinc-900">Thumbs-down answers</p>
            </div>
            {data.negative_feedback.length === 0 ? (
              <p className="text-xs text-zinc-400">No negative feedback this week.</p>
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
