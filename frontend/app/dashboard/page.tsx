"use client"

import * as React from "react"
import { ArrowUp, ArrowDown, Minus, RefreshCw, AlertTriangle, ThumbsDown, Loader2, MessageSquare } from "lucide-react"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface IntentRow { intent: string; label: string; count: number; example: string; trend: "up" | "down" | "flat"; prev_count: number }
interface UnansweredGroup { theme: string; count: number; examples: string[] }
interface NegativeItem { question: string; answer: string; department: string }
interface TopQuestion { question: string; count: number }

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
  top_questions: TopQuestion[]
  unanswered: UnansweredGroup[]
  negative_feedback: NegativeItem[]
}

function Trend({ t }: { t: "up" | "down" | "flat" }) {
  if (t === "up")   return <ArrowUp className="size-3 text-emerald-500" />
  if (t === "down") return <ArrowDown className="size-3 text-red-400" />
  return <Minus className="size-3 text-zinc-300" />
}

const INTENT_SHORT: Record<string, string> = {
  "Prerequisites & Course Requirements": "Prereqs",
  "Program Requirements":                "Programs",
  "Deadlines & Dates":                   "Deadlines",
  "Course Lookups":                      "Courses",
  "Registration Procedures":             "Reg.",
  "Academic Regulations & GPA":          "GPA",
  "Services & Campus Life":              "Services",
  "General / Other":                     "Other",
}

function CategoryChart({ intents }: { intents: IntentRow[] }) {
  if (!intents || intents.length === 0) return (
    <div className="flex items-center justify-center flex-1 text-xs text-zinc-400">No data yet.</div>
  )
  const max = Math.max(...intents.map(r => r.count), 1)
  return (
    <div className="flex items-end gap-1.5 flex-1 w-full min-h-0">
      {intents.map((r) => {
        const pct = r.count / max
        const shortLabel = INTENT_SHORT[r.label] ?? r.label.split(" ")[0]
        return (
          <div key={r.intent} className="flex-1 flex flex-col items-center gap-1 group relative h-full justify-end">
            <div className="absolute -top-7 left-1/2 -translate-x-1/2 bg-zinc-900 text-white text-[10px] rounded px-1.5 py-0.5 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
              {r.label}: {r.count}
            </div>
            <div
              className="w-full rounded-t-sm bg-zinc-800 hover:bg-zinc-600 transition-colors cursor-default"
              style={{ height: `${Math.max(pct * 100, 6)}px` }}
            />
            <span className="text-[8px] text-zinc-400 text-center leading-tight w-full truncate px-0.5">{shortLabel}</span>
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
      <div className="h-screen bg-[#F7F5F0] flex items-center justify-center">
        <div className="flex items-center gap-2 text-zinc-400 text-sm">
          <Loader2 className="size-4 animate-spin" /> Loading dashboard…
        </div>
      </div>
    )
  }

  if (error && !data) {
    return (
      <div className="h-screen bg-[#F7F5F0] flex items-center justify-center px-5">
        <div className="text-center">
          <p className="text-sm text-zinc-600 mb-3">{error}</p>
          <button onClick={() => load(selectedDays)} className="text-sm text-zinc-900 underline underline-offset-2">Retry</button>
        </div>
      </div>
    )
  }

  if (!data) return null
  const s = data.snapshot

  const headlineParts = [
    `${s.total_questions.toLocaleString()} questions asked`,
    s.accuracy !== null ? `${s.accuracy}% rated helpful` : null,
    s.top_department !== "—" ? `most from ${s.top_department}` : null,
  ].filter(Boolean).join(" · ")

  const timeLabel = selectedDays === 0 ? "all time" : selectedDays === 1 ? "last 24 hours" : `last ${selectedDays} days`

  return (
    <div className="h-screen bg-[#F7F5F0] text-zinc-900 flex flex-col overflow-hidden">

      {/* Fixed header */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-zinc-200 bg-[#F7F5F0] shrink-0">
        <div>
          <h1 className="text-base font-bold tracking-tight">CampusQ — Advisor Dashboard</h1>
          <p className="text-xs text-zinc-500">Anonymized · {timeLabel}</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <select
              value={selectedDays}
              onChange={(e) => handleTimeframe(Number(e.target.value))}
              className="appearance-none bg-white border border-zinc-200 rounded-lg px-3 py-1.5 pr-8 text-sm text-zinc-700 font-medium shadow-sm hover:border-zinc-300 focus:outline-none cursor-pointer transition-colors"
            >
              {TIMEFRAMES.map((tf) => (
                <option key={tf.days} value={tf.days}>{tf.label}</option>
              ))}
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-2 flex items-center">
              <svg className="size-3 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>
          <button
            onClick={() => load(selectedDays)}
            className="inline-flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-900 bg-white border border-zinc-200 rounded-lg px-3 py-1.5 shadow-sm hover:border-zinc-300 transition-colors"
          >
            <RefreshCw className={`size-3 ${loading ? "animate-spin" : ""}`} /> Refresh
          </button>
        </div>
      </div>

      {/* Main grid — fills remaining height */}
      <div className="flex-1 min-h-0 p-4 grid grid-cols-12 grid-rows-2 gap-3">

        {/* Headline — full width top row col 1-12 row 1 */}
        <div className="col-span-12 row-span-1 grid grid-cols-12 gap-3">

          {/* Headline dark card */}
          <div className="col-span-4 bg-zinc-900 text-white rounded-2xl px-5 py-4 flex flex-col justify-between">
            <p className="text-[10px] font-semibold uppercase tracking-widest text-zinc-500">Summary</p>
            <p className="text-sm font-medium leading-snug mt-1">{headlineParts || "No data yet."}</p>
            <p className="text-[10px] text-zinc-600 mt-2">All data anonymized · no individual tracking</p>
          </div>

          {/* 3 stat cards */}
          {[
            { label: "Questions asked", value: s.total_questions.toLocaleString(), sub: timeLabel },
            { label: "Helpfulness rate", value: s.accuracy !== null ? `${s.accuracy}%` : "—", sub: s.accuracy !== null ? `${s.thumbs_up} 👍  ${s.thumbs_down} 👎` : "no ratings yet" },
            { label: "Top department", value: s.top_department, sub: "by volume" },
          ].map((st) => (
            <div key={st.label} className="col-span-2 bg-white border border-zinc-200 rounded-2xl px-4 py-3 flex flex-col justify-between">
              <p className="text-[10px] font-medium uppercase tracking-wider text-zinc-400">{st.label}</p>
              <p className="text-2xl font-bold text-zinc-900 tabular-nums truncate">{st.value}</p>
              <p className="text-[10px] text-zinc-400">{st.sub}</p>
            </div>
          ))}

          {/* Category chart */}
          <div className="col-span-4 bg-white border border-zinc-200 rounded-2xl p-4 flex flex-col">
            <p className="text-[10px] font-semibold uppercase tracking-widest text-zinc-400 mb-2 shrink-0">What students are confused about</p>
            <div className="flex-1 min-h-0 flex items-end gap-1.5 pt-6">
              <CategoryChart intents={data.intents} />
            </div>
          </div>
        </div>

        {/* Bottom row */}
        <div className="col-span-12 row-span-1 grid grid-cols-12 gap-3 min-h-0">

          {/* Top questions */}
          <div className="col-span-4 bg-white border border-zinc-200 rounded-2xl flex flex-col overflow-hidden">
            <p className="text-[10px] font-semibold uppercase tracking-widest text-zinc-400 px-4 pt-4 pb-2 shrink-0">Top questions</p>
            <div className="flex-1 overflow-y-auto divide-y divide-zinc-100">
              {data.top_questions?.length === 0 ? (
                <p className="text-xs text-zinc-400 px-4 py-3">No data yet.</p>
              ) : data.top_questions?.map((q, i) => (
                <div key={i} className="flex items-start gap-2 px-4 py-2.5">
                  <MessageSquare className="size-3 text-zinc-300 mt-0.5 shrink-0" />
                  <p className="flex-1 text-xs text-zinc-700 leading-snug line-clamp-2">"{q.question}"</p>
                  {q.count > 1 && <span className="text-[10px] text-zinc-400 shrink-0">×{q.count}</span>}
                </div>
              ))}
            </div>
          </div>

          {/* Categories list */}
          <div className="col-span-4 bg-white border border-zinc-200 rounded-2xl flex flex-col overflow-hidden">
            <p className="text-[10px] font-semibold uppercase tracking-widest text-zinc-400 px-4 pt-4 pb-2 shrink-0">By category</p>
            <div className="flex-1 overflow-y-auto divide-y divide-zinc-100">
              {data.intents.length === 0 ? (
                <p className="text-xs text-zinc-400 px-4 py-3">No data yet.</p>
              ) : data.intents.map((r) => (
                <div key={r.intent} className="flex items-center gap-2 px-4 py-2.5">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1">
                      <span className="text-xs font-medium text-zinc-900 truncate">{r.label}</span>
                      <Trend t={r.trend} />
                    </div>
                    {r.example && <p className="text-[10px] text-zinc-400 truncate">"{r.example}"</p>}
                  </div>
                  <span className="text-sm font-bold text-zinc-900 tabular-nums shrink-0">{r.count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Failing section */}
          <div className="col-span-2 bg-white border border-zinc-200 rounded-2xl flex flex-col overflow-hidden">
            <div className="flex items-center gap-1.5 px-4 pt-4 pb-2 shrink-0">
              <AlertTriangle className="size-3 text-amber-500" />
              <p className="text-[10px] font-semibold uppercase tracking-widest text-zinc-400">Unanswered</p>
            </div>
            <div className="flex-1 overflow-y-auto px-4 pb-3">
              {data.unanswered.length === 0 ? (
                <p className="text-xs text-zinc-400">Every question found an answer.</p>
              ) : data.unanswered.map((g) => (
                <div key={g.theme} className="mb-2">
                  <p className="text-[10px] font-medium text-zinc-700">{g.theme} <span className="text-zinc-400">({g.count})</span></p>
                  {g.examples.slice(0, 2).map((ex, j) => (
                    <p key={j} className="text-[10px] text-zinc-400 truncate pl-2">· {ex}</p>
                  ))}
                </div>
              ))}
            </div>
          </div>

          <div className="col-span-2 bg-white border border-zinc-200 rounded-2xl flex flex-col overflow-hidden">
            <div className="flex items-center gap-1.5 px-4 pt-4 pb-2 shrink-0">
              <ThumbsDown className="size-3 text-red-400" />
              <p className="text-[10px] font-semibold uppercase tracking-widest text-zinc-400">Thumbs down</p>
            </div>
            <div className="flex-1 overflow-y-auto px-4 pb-3 space-y-2">
              {data.negative_feedback.length === 0 ? (
                <p className="text-xs text-zinc-400">No negative feedback.</p>
              ) : data.negative_feedback.map((n, i) => (
                <div key={i} className="border-l-2 border-red-200 pl-2">
                  <p className="text-[10px] font-medium text-zinc-700 line-clamp-1">{n.question}</p>
                  <p className="text-[10px] text-zinc-400 line-clamp-2">{n.answer}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
