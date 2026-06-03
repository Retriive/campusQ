"use client"

import * as React from "react"
import { Loader2, ArrowLeft, Search, ChevronRight, Check, GraduationCap, ListChecks } from "lucide-react"
import { cn } from "@/lib/utils"
import { useCampus } from "./campus-context"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface Course { code: string; title: string; credits: number | null }
interface ReqGroup { instruction: string; credits: number | null; courses: Course[] }
interface ProgramIndex { slug: string; variants: string[] }

// Derive a clean program display name from a variant heading by cutting at the
// first degree token (e.g. "Computer Science B.C.S. Honours (20)" -> "Computer Science").
const DEGREE_TOKEN = /\b(B\.[A-Za-z.]+|Bachelor|Honours|Major|Minor|Stream|Concentration|Specialization|Certificate|Post-Baccalaureate|Diploma)\b/
function programName(variants: string[]): string {
  const base = variants[0] || ""
  const m = base.match(DEGREE_TOKEN)
  const name = (m && m.index ? base.slice(0, m.index) : base).trim()
  return name || base.replace(/\(.*?\)/g, "").trim() || base
}
function cleanVariant(v: string): string {
  return v.replace(/\s*\(\d+\.?\d*\s*credits?\)/i, "").trim()
}
function totalTarget(variant: string): number | null {
  const m = variant.match(/\((\d+\.?\d*)\s*credits?\)/i)
  return m ? parseFloat(m[1]) : null
}

export function RequirementTracker() {
  const { theme } = useCampus()
  const [index, setIndex] = React.useState<ProgramIndex[]>([])
  const [loadingIndex, setLoadingIndex] = React.useState(true)
  const [search, setSearch] = React.useState("")

  const [slug, setSlug] = React.useState<string | null>(null)
  const [variants, setVariants] = React.useState<string[]>([])
  const [groupsByVariant, setGroupsByVariant] = React.useState<Record<string, ReqGroup[]>>({})
  const [loadingProgram, setLoadingProgram] = React.useState(false)
  const [variant, setVariant] = React.useState<string | null>(null)

  const [checked, setChecked] = React.useState<Set<string>>(new Set())
  const [onlyRemaining, setOnlyRemaining] = React.useState(false)

  // load program index
  React.useEffect(() => {
    fetch(`${API_URL}/api/program-requirements`)
      .then((r) => r.json())
      .then((d) => setIndex(d.programs || []))
      .catch(() => {})
      .finally(() => setLoadingIndex(false))
  }, [])

  // persistence key per variant
  const storeKey = slug && variant ? `campusq-track::${slug}::${variant}` : null
  React.useEffect(() => {
    if (!storeKey) return
    try {
      const raw = localStorage.getItem(storeKey)
      setChecked(new Set(raw ? JSON.parse(raw) : []))
    } catch { setChecked(new Set()) }
  }, [storeKey])
  const persist = (next: Set<string>) => {
    setChecked(next)
    if (storeKey) localStorage.setItem(storeKey, JSON.stringify([...next]))
  }

  const openProgram = async (s: string) => {
    setSlug(s); setVariant(null); setLoadingProgram(true)
    try {
      const d = await fetch(`${API_URL}/api/program-requirements?slug=${encodeURIComponent(s)}`).then((r) => r.json())
      if (d.found) {
        setVariants(Object.keys(d.variants))
        setGroupsByVariant(d.variants)
      }
    } catch {} finally { setLoadingProgram(false) }
  }

  const toggle = (code: string) => {
    const next = new Set(checked)
    next.has(code) ? next.delete(code) : next.add(code)
    persist(next)
  }

  // ── Tracker view ───────────────────────────────────────────────────────────
  if (slug && variant) {
    const groups = groupsByVariant[variant] || []
    const allCourses = groups.flatMap((g) => g.courses)
    const target = totalTarget(variant) ?? allCourses.reduce((s, c) => s + (c.credits || 0), 0)
    const done = allCourses.filter((c) => checked.has(c.code)).reduce((s, c) => s + (c.credits || 0), 0)
    const pct = target > 0 ? Math.min(done / target, 1) : 0

    return (
      <div className="flex flex-col gap-5">
        <div className="flex items-center gap-3">
          <button onClick={() => setVariant(null)} className="size-8 flex items-center justify-center rounded-lg hover:bg-secondary text-muted-foreground">
            <ArrowLeft className="size-4" />
          </button>
          <div className="min-w-0 flex-1">
            <p className="text-xs text-muted-foreground">{programName(variants)}</p>
            <h2 className="text-base font-semibold truncate">{cleanVariant(variant)}</h2>
          </div>
        </div>

        {/* Overall progress */}
        <div className="rounded-2xl border border-border bg-card p-5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Degree progress</span>
            <span className="text-sm font-bold tabular-nums">{done.toFixed(1)} / {target.toFixed(1)} cr</span>
          </div>
          <div className="h-3 rounded-full bg-secondary overflow-hidden">
            <div className={cn("h-full rounded-full transition-all duration-500", theme.bgClass)} style={{ width: `${pct * 100}%` }} />
          </div>
          <div className="flex items-center justify-between mt-3">
            <span className="text-xs text-muted-foreground">{Math.round(pct * 100)}% complete</span>
            <button
              onClick={() => setOnlyRemaining((v) => !v)}
              className={cn("flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-lg transition-colors",
                onlyRemaining ? cn(theme.bgClass, "text-white") : "border border-border text-muted-foreground hover:text-foreground")}
            >
              <ListChecks className="size-3" /> {onlyRemaining ? "Showing remaining" : "Show what's left"}
            </button>
          </div>
        </div>

        {/* Requirement groups */}
        <div className="space-y-4">
          {groups.map((g, gi) => {
            const visible = onlyRemaining ? g.courses.filter((c) => !checked.has(c.code)) : g.courses
            if (onlyRemaining && visible.length === 0) return null
            const gDone = g.courses.filter((c) => checked.has(c.code)).reduce((s, c) => s + (c.credits || 0), 0)
            return (
              <div key={gi} className="rounded-xl border border-border bg-card overflow-hidden">
                <div className="px-4 py-3 border-b border-border/50 bg-secondary/20">
                  <div className="flex items-start justify-between gap-3">
                    <p className="text-sm font-medium text-foreground leading-snug">{g.instruction || "Required courses"}</p>
                    {g.credits != null && (
                      <span className="shrink-0 text-[11px] font-mono px-1.5 py-0.5 rounded-md bg-secondary text-muted-foreground">
                        {gDone.toFixed(1)}/{g.credits}
                      </span>
                    )}
                  </div>
                </div>
                <div className="p-2 grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                  {visible.map((c) => {
                    const on = checked.has(c.code)
                    return (
                      <button
                        key={c.code + c.title}
                        onClick={() => toggle(c.code)}
                        className={cn("flex items-center gap-2.5 px-3 py-2 rounded-lg border text-left transition-all",
                          on ? "border-emerald-500/40 bg-emerald-500/10" : "border-border hover:bg-secondary/40")}
                      >
                        <span className={cn("size-4 rounded-md border flex items-center justify-center shrink-0 transition-colors",
                          on ? "bg-emerald-500 border-emerald-500" : "border-muted-foreground/30")}>
                          {on && <Check className="size-3 text-white" strokeWidth={3} />}
                        </span>
                        <span className="min-w-0 flex-1">
                          <span className={cn("text-xs font-mono font-semibold block", on ? "text-emerald-700 dark:text-emerald-400" : "text-foreground")}>{c.code}</span>
                          {c.title && <span className="text-[11px] text-muted-foreground truncate block">{c.title}</span>}
                        </span>
                        {c.credits != null && <span className="text-[10px] text-muted-foreground/50 shrink-0">{c.credits}</span>}
                      </button>
                    )
                  })}
                </div>
              </div>
            )
          })}
        </div>

        <p className="text-[11px] text-muted-foreground/50">
          Based on the current Carleton calendar. Compound rules (e.g. "one of A or B") and program exceptions apply — verify with your advisor.
        </p>
      </div>
    )
  }

  // ── Variant picker ─────────────────────────────────────────────────────────
  if (slug) {
    return (
      <div className="flex flex-col gap-5">
        <div className="flex items-center gap-3">
          <button onClick={() => { setSlug(null); setVariants([]) }} className="size-8 flex items-center justify-center rounded-lg hover:bg-secondary text-muted-foreground">
            <ArrowLeft className="size-4" />
          </button>
          <h2 className="text-lg font-semibold">{programName(variants)}</h2>
        </div>
        {loadingProgram ? (
          <div className="flex items-center gap-2 text-muted-foreground py-12 justify-center text-sm">
            <Loader2 className="size-4 animate-spin" /> Loading…
          </div>
        ) : (
          <>
            <p className="text-sm text-muted-foreground">Pick your degree variant to start tracking.</p>
            <div className="space-y-1.5">
              {variants.map((v) => (
                <button key={v} onClick={() => setVariant(v)}
                  className="w-full flex items-center justify-between gap-3 px-4 py-3 rounded-xl border border-border bg-card hover:bg-secondary/40 transition-all text-left group">
                  <span className="text-sm text-foreground">{cleanVariant(v)}</span>
                  <ChevronRight className="size-3.5 text-muted-foreground/30 group-hover:text-muted-foreground" />
                </button>
              ))}
            </div>
          </>
        )}
      </div>
    )
  }

  // ── Program picker ─────────────────────────────────────────────────────────
  const enriched = index.map((p) => ({ ...p, name: programName(p.variants) }))
    .sort((a, b) => a.name.localeCompare(b.name))
  const results = search.trim()
    ? enriched.filter((p) => p.name.toLowerCase().includes(search.toLowerCase()))
    : enriched

  return (
    <div className="flex flex-col gap-5">
      <div>
        <div className="flex items-center gap-2 mb-0.5">
          <GraduationCap className={cn("size-4", theme.textClass)} />
          <h2 className="text-lg font-semibold">My Degree</h2>
        </div>
        <p className="text-sm text-muted-foreground">Track your progress — check off completed courses and see what's left.</p>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-3.5 text-muted-foreground/40" />
        <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search your program…"
          className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-border bg-card text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 placeholder:text-muted-foreground/40" />
      </div>

      {loadingIndex ? (
        <div className="flex items-center gap-2 text-muted-foreground py-12 justify-center text-sm">
          <Loader2 className="size-4 animate-spin" /> Loading programs…
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
          {results.map((p) => (
            <button key={p.slug} onClick={() => openProgram(p.slug)}
              className="group flex items-center justify-between gap-3 px-4 py-3 rounded-xl border border-border bg-card hover:bg-secondary/40 transition-all text-left">
              <span className="min-w-0">
                <span className="text-sm font-medium text-foreground truncate block">{p.name}</span>
                <span className="text-xs text-muted-foreground">{p.variants.length} variant{p.variants.length !== 1 ? "s" : ""}</span>
              </span>
              <ChevronRight className="size-3.5 text-muted-foreground/30 group-hover:text-muted-foreground shrink-0" />
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
