"use client"

import * as React from "react"
import { ArrowUp, ArrowDown, Minus, RefreshCw, AlertTriangle, ThumbsDown, Loader2, MessageSquare } from "lucide-react"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface IntentRow { intent: string; label: string; count: number; example: string; trend: "up" | "down" | "flat"; prev_count: number }
interface UnansweredGroup { theme: string; count: number; examples: string[] }
interface NegativeItem { question: string; answer: string; department: string }
interface TopQuestion { question: string; count: number }

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
    <div className="flex items-center justify-center h-full text-xs text-zinc-400">No data yet.</div>
  )
  const max = Math.max(...intents.map(r => r.count), 1)
  return (
    <div className="flex items-end gap-2 h-full w-full">
      {intents.map((r) => {
        const pct = r.count / max
        const shortLabel = INTENT_SHORT[r.label] ?? r.label.split(" ")[0]
        return (
          <div key={r.intent} className="flex-1 flex flex-col items-center gap-1 group relative h-full justify-end">
            <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-zinc-900 text-white text-[10px] rounded-md px-2 py-1 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10 shadow-lg">
              {r.label}: {r.count}
            </div>
            <div
              className="w-full rounded-t-[3px] bg-zinc-900 hover:bg-zinc-700 transition-colors cursor-default"
              style={{ height: `${Math.max(pct * 90, 4)}px` }}
            />
            <span className="text-[9px] text-zinc-400 text-center leading-tight w-full truncate">{shortLabel}</span>
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
    <div className="h-screen bg-white flex items-center justify-center">
      <Loader2 className="size-4 animate-spin text-zinc-300" />
    </div>
  )

  if (error && !data) return (
    <div className="h-screen bg-white flex items-center justify-center">
      <div className="text-center space-y-2">
        <p className="text-sm text-zinc-400">{error}</p>
        <button onClick={() => load(selectedDays)} className="text-xs text-zinc-900 underline">Retry</button>
      </div>
    </div>
  )

  if (!data) return null
  const s = data.snapshot

  return (
    <div className="h-screen bg-white text-zinc-900 flex flex-col overflow-hidden">

      {/* Header */}
      <header className="shrink-0 flex items-center justify-between px-8 h-14 border-b border-zinc-100">
        <div className="flex items-center gap-3">
          <span className="text-sm font-semibold tracking-tight">CampusQ</span>
          <span className="text-zinc-200 text-sm">·</span>
          <span className="text-sm text-zinc-400">Advisor Dashboard</span>
        </div>
        <div className="flex items-center gap-1">
          {TIMEFRAMES.map((tf) => (
            <button
              key={tf.days}
              onClick={() => handleTimeframe(tf.days)}
              className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                selectedDays === tf.days
                  ? "bg-zinc-900 text-white"
                  : "text-zinc-400 hover:text-zinc-900 hover:bg-zinc-50"
              }`}
            >
              {tf.label}
            </button>
          ))}
          <div className="w-px h-4 bg-zinc-100 mx-1" />
          <button
            onClick={() => load(selectedDays)}
            className="p-1.5 rounded-md text-zinc-400 hover:text-zinc-900 hover:bg-zinc-50 transition-colors"
          >
            <RefreshCw className={`size-3.5 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </header>

      {/* Body */}
      <div className="flex-1 min-h-0 grid grid-cols-12 grid-rows-2 gap-px bg-zinc-100 p-px">

        {/* ── Top row ── */}

        {/* Stat: Questions */}
        <div className="col-span-2 row-span-1 bg-white p-6 flex flex-col justify-between">
          <p className="text-xs text-zinc-400 font-medium">Questions asked</p>
          <div>
            <p className="text-4xl font-bold tracking-tight">{s.total_questions.toLocaleString()}</p>
            <p className="text-xs text-zinc-400 mt-1">
              {selectedDays === 0 ? "all time" : selectedDays === 1 ? "last 24 hours" : `last ${selectedDays} days`}
            </p>
          </div>
        </div>

        {/* Stat: Helpfulness */}
        <div className="col-span-2 row-span-1 bg-white p-6 flex flex-col justify-between">
          <p className="text-xs text-zinc-400 font-medium">Helpfulness rate</p>
          <div>
            <p className="text-4xl font-bold tracking-tight">
              {s.accuracy !== null ? `${s.accuracy}%` : "—"}
            </p>
            <p className="text-xs text-zinc-400 mt-1">
              {s.accuracy !== null ? `${s.thumbs_up} up · ${s.thumbs_down} down` : "no ratings yet"}
            </p>
          </div>
        </div>

        {/* Stat: Top dept */}
        <div className="col-span-2 row-span-1 bg-white p-6 flex flex-col justify-between">
          <p className="text-xs text-zinc-400 font-medium">Top department</p>
          <div>
            <p className="text-2xl font-bold tracking-tight leading-tight">{s.top_department}</p>
            <p className="text-xs text-zinc-400 mt-1">by question volume</p>
          </div>
        </div>

        {/* Category chart */}
        <div className="col-span-6 row-span-1 bg-white p-6 flex flex-col">
          <p className="text-xs text-zinc-400 font-medium mb-4 shrink-0">What students are confused about</p>
          <div className="flex-1 min-h-0">
            <CategoryChart intents={data.intents} />
          </div>
        </div>

        {/* ── Bottom row ── */}

        {/* Top questions */}
        <div className="col-span-4 row-span-1 bg-white flex flex-col overflow-hidden">
          <div className="px-6 pt-5 pb-3 shrink-0">
            <p className="text-xs text-zinc-400 font-medium">Top questions</p>
          </div>
          <div className="flex-1 overflow-y-auto">
            {!data.top_questions?.length ? (
              <p className="text-xs text-zinc-300 px-6">No data yet.</p>
            ) : data.top_questions.map((q, i) => (
              <div key={i} className={`flex items-start gap-3 px-6 py-3 ${i < data.top_questions.length - 1 ? "border-b border-zinc-50" : ""}`}>
                <MessageSquare className="size-3.5 text-zinc-200 mt-0.5 shrink-0" />
                <p className="flex-1 text-xs text-zinc-600 leading-relaxed line-clamp-2">"{q.question}"</p>
                {q.count > 1 && <span className="text-[10px] text-zinc-300 shrink-0 tabular-nums">×{q.count}</span>}
              </div>
            ))}
          </div>
        </div>

        {/* Category list */}
        <div className="col-span-4 row-span-1 bg-white flex flex-col overflow-hidden">
          <div className="px-6 pt-5 pb-3 shrink-0">
            <p className="text-xs text-zinc-400 font-medium">By category</p>
          </div>
          <div className="flex-1 overflow-y-auto">
            {data.intents.length === 0 ? (
              <p className="text-xs text-zinc-300 px-6">No data yet.</p>
            ) : data.intents.map((r, i) => (
              <div key={r.intent} className={`flex items-center gap-3 px-6 py-2.5 ${i < data.intents.length - 1 ? "border-b border-zinc-50" : ""}`}>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-medium text-zinc-800 truncate">{r.label}</span>
                    <Trend t={r.trend} />
                  </div>
                  {r.example && <p className="text-[10px] text-zinc-400 truncate mt-0.5">"{r.example}"</p>}
                </div>
                <span className="text-sm font-semibold text-zinc-900 tabular-nums shrink-0">{r.count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Failing */}
        <div className="col-span-4 row-span-1 bg-white flex flex-col overflow-hidden">
          <div className="px-6 pt-5 pb-3 shrink-0">
            <p className="text-xs text-zinc-400 font-medium">Needs attention</p>
          </div>
          <div className="flex-1 overflow-y-auto px-6 pb-4 space-y-4">

            {/* Unanswered */}
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <AlertTriangle className="size-3 text-amber-400" />
                <p className="text-[10px] font-semibold uppercase tracking-widest text-zinc-400">Unanswered</p>
              </div>
              {data.unanswered.length === 0 ? (
                <p className="text-xs text-zinc-300">Every question found an answer.</p>
              ) : data.unanswered.map((g) => (
                <div key={g.theme} className="mb-2">
                  <p className="text-xs font-medium text-zinc-700">{g.theme} <span className="text-zinc-400 font-normal">({g.count})</span></p>
                  {g.examples.slice(0, 2).map((ex, j) => (
                    <p key={j} className="text-[10px] text-zinc-400 truncate pl-2 mt-0.5">· {ex}</p>
                  ))}
                </div>
              ))}
            </div>

            {/* Thumbs down */}
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <ThumbsDown className="size-3 text-red-400" />
                <p className="text-[10px] font-semibold uppercase tracking-widest text-zinc-400">Thumbs down</p>
              </div>
              {data.negative_feedback.length === 0 ? (
                <p className="text-xs text-zinc-300">No negative feedback.</p>
              ) : data.negative_feedback.map((n, i) => (
                <div key={i} className="border-l-2 border-zinc-100 pl-3 mb-2">
                  <p className="text-xs font-medium text-zinc-700 line-clamp-1">{n.question}</p>
                  <p className="text-[10px] text-zinc-400 line-clamp-2 mt-0.5">{n.answer}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="shrink-0 px-8 py-2 border-t border-zinc-100">
        <p className="text-[10px] text-zinc-300">All data is aggregated and anonymized. No student names, IDs, or individual tracking.</p>
      </div>
    </div>
  )
}
