"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { useCampus } from "./campus-context"
import { CalendarDays, Clock, ChevronDown, ChevronUp } from "lucide-react"

type Term = "Summer 2026" | "Fall 2026" | "Winter 2027"
type Category = "registration" | "withdrawal" | "exams" | "payment" | "classes" | "holiday"

interface Deadline {
  id: string
  title: string
  date: string // YYYY-MM-DD
  term: Term
  category: Category
  note?: string
}

const DEADLINES: Deadline[] = [
  // ── Summer 2026 ────────────────────────────────────────────────────────────
  { id: "su26-term-begins",       title: "Summer term begins",                               date: "2026-05-06", term: "Summer 2026", category: "classes" },
  { id: "su26-early-add",         title: "Last day to add/change early summer courses",       date: "2026-05-12", term: "Summer 2026", category: "registration" },
  { id: "su26-full-add",          title: "Last day to add full summer courses",               date: "2026-05-20", term: "Summer 2026", category: "registration" },
  { id: "su26-full-fee",          title: "Last day to drop full summer (full refund)",        date: "2026-05-31", term: "Summer 2026", category: "withdrawal" },
  { id: "su26-early-withdraw",    title: "Last day to withdraw from early summer courses",    date: "2026-06-01", term: "Summer 2026", category: "withdrawal" },
  { id: "su26-payment",           title: "Summer final payment deadline",                     date: "2026-06-25", term: "Summer 2026", category: "payment" },
  { id: "su26-early-lastday",     title: "Last day of early summer classes",                  date: "2026-06-18", term: "Summer 2026", category: "classes" },
  { id: "su26-early-exams",       title: "Early summer final exams begin",                    date: "2026-06-21", term: "Summer 2026", category: "exams" },
  { id: "su26-late-begins",       title: "Late summer courses begin",                         date: "2026-07-02", term: "Summer 2026", category: "classes" },
  { id: "su26-late-add",          title: "Last day to add/change late summer courses",        date: "2026-07-08", term: "Summer 2026", category: "registration" },
  { id: "su26-canada-day",        title: "Canada Day — University closed",                    date: "2026-07-01", term: "Summer 2026", category: "holiday" },
  { id: "su26-full-withdraw",     title: "Last day to withdraw from full/late summer courses",date: "2026-08-01", term: "Summer 2026", category: "withdrawal" },
  { id: "su26-civic",             title: "Civic Holiday — University closed",                 date: "2026-08-03", term: "Summer 2026", category: "holiday" },
  { id: "su26-late-lastday",      title: "Last day of late/full summer classes",              date: "2026-08-14", term: "Summer 2026", category: "classes" },
  { id: "su26-final-exams",       title: "Full/late summer final exams begin",                date: "2026-08-17", term: "Summer 2026", category: "exams" },

  // ── Fall 2026 ──────────────────────────────────────────────────────────────
  { id: "fa26-timetickets",       title: "Time tickets available in Carleton Central",        date: "2026-06-17", term: "Fall 2026", category: "registration" },
  { id: "fa26-reg-new",           title: "Registration opens — new first-year students",      date: "2026-07-06", term: "Fall 2026", category: "registration" },
  { id: "fa26-reg-returning",     title: "Registration opens — returning students",           date: "2026-07-10", term: "Fall 2026", category: "registration" },
  { id: "fa26-reg-special",       title: "Registration opens — special/visiting students",    date: "2026-08-05", term: "Fall 2026", category: "registration" },
  { id: "fa26-payment",           title: "Fall payment deadline",                             date: "2026-08-25", term: "Fall 2026", category: "payment" },
  { id: "fa26-labour-day",        title: "Labour Day — University closed",                    date: "2026-09-07", term: "Fall 2026", category: "holiday" },
  { id: "fa26-term-begins",       title: "Fall term begins",                                  date: "2026-09-09", term: "Fall 2026", category: "classes" },
  { id: "fa26-early-add",         title: "Last day to add/change early fall courses",         date: "2026-09-15", term: "Fall 2026", category: "registration" },
  { id: "fa26-full-add",          title: "Last day to add full fall / fall-winter courses",   date: "2026-09-22", term: "Fall 2026", category: "registration" },
  { id: "fa26-full-fee",          title: "Last day to drop full fall courses (full refund)",  date: "2026-09-30", term: "Fall 2026", category: "withdrawal" },
  { id: "fa26-early-withdraw",    title: "Last day to withdraw from early fall courses",      date: "2026-10-01", term: "Fall 2026", category: "withdrawal" },
  { id: "fa26-thanksgiving",      title: "Thanksgiving — University closed",                  date: "2026-10-12", term: "Fall 2026", category: "holiday" },
  { id: "fa26-early-lastday",     title: "Last day of early fall classes",                    date: "2026-10-23", term: "Fall 2026", category: "classes" },
  { id: "fa26-fall-break",        title: "Fall break begins (no classes)",                    date: "2026-10-26", term: "Fall 2026", category: "holiday" },
  { id: "fa26-early-exams",       title: "Early fall final exams begin",                      date: "2026-10-31", term: "Fall 2026", category: "exams" },
  { id: "fa26-late-begins",       title: "Late fall classes begin",                           date: "2026-11-02", term: "Fall 2026", category: "classes" },
  { id: "fa26-full-withdraw",     title: "Last day to withdraw from full/late fall courses",  date: "2026-11-15", term: "Fall 2026", category: "withdrawal" },
  { id: "fa26-winter-payment",    title: "Winter payment deadline",                           date: "2026-11-25", term: "Fall 2026", category: "payment" },
  { id: "fa26-lastday",           title: "Last day of full/late fall classes",                date: "2026-12-11", term: "Fall 2026", category: "classes" },
  { id: "fa26-exams",             title: "Fall final exams begin",                            date: "2026-12-12", term: "Fall 2026", category: "exams" },
  { id: "fa26-uni-closed",        title: "University closes for holidays",                    date: "2026-12-24", term: "Fall 2026", category: "holiday" },

  // ── Winter 2027 ────────────────────────────────────────────────────────────
  { id: "wi27-term-begins",       title: "Winter term begins",                                date: "2027-01-06", term: "Winter 2027", category: "classes" },
  { id: "wi27-early-add",         title: "Last day to add/change early winter courses",       date: "2027-01-12", term: "Winter 2027", category: "registration" },
  { id: "wi27-full-add",          title: "Last day to add full winter courses",               date: "2027-01-19", term: "Winter 2027", category: "registration" },
  { id: "wi27-full-fee",          title: "Last day to drop full winter (full refund)",        date: "2027-01-31", term: "Winter 2027", category: "withdrawal" },
  { id: "wi27-early-withdraw",    title: "Last day to withdraw from early winter courses",    date: "2027-02-01", term: "Winter 2027", category: "withdrawal" },
  { id: "wi27-family-day",        title: "Family Day — University closed",                    date: "2027-02-15", term: "Winter 2027", category: "holiday" },
  { id: "wi27-reading-week",      title: "Winter break / Reading week begins",                date: "2027-02-15", term: "Winter 2027", category: "holiday" },
  { id: "wi27-late-begins",       title: "Late winter classes begin",                         date: "2027-02-25", term: "Winter 2027", category: "classes" },
  { id: "wi27-full-withdraw",     title: "Last day to withdraw from full/late winter courses",date: "2027-03-15", term: "Winter 2027", category: "withdrawal" },
  { id: "wi27-good-friday",       title: "Good Friday — University closed",                   date: "2027-03-26", term: "Winter 2027", category: "holiday" },
  { id: "wi27-lastday",           title: "Last day of winter classes",                        date: "2027-04-09", term: "Winter 2027", category: "classes" },
  { id: "wi27-exams",             title: "Winter final exams begin",                          date: "2027-04-11", term: "Winter 2027", category: "exams" },
  { id: "wi27-takeHome-due",      title: "All take-home exams due",                           date: "2027-04-23", term: "Winter 2027", category: "exams" },
]

const CATEGORY_CONFIG: Record<Category, { label: string; color: string; bg: string }> = {
  registration: { label: "Registration", color: "text-blue-600 dark:text-blue-400",   bg: "bg-blue-500/10"   },
  withdrawal:   { label: "Withdrawal",   color: "text-orange-600 dark:text-orange-400", bg: "bg-orange-500/10" },
  exams:        { label: "Exams",        color: "text-purple-600 dark:text-purple-400", bg: "bg-purple-500/10" },
  payment:      { label: "Payment",      color: "text-red-500 dark:text-red-400",      bg: "bg-red-500/10"    },
  classes:      { label: "Classes",      color: "text-emerald-600 dark:text-emerald-400", bg: "bg-emerald-500/10" },
  holiday:      { label: "Holiday",      color: "text-muted-foreground",               bg: "bg-secondary"     },
}

const TERM_ORDER: Term[] = ["Summer 2026", "Fall 2026", "Winter 2027"]

function parseDate(dateStr: string): Date {
  const [y, m, d] = dateStr.split("-").map(Number)
  return new Date(y, m - 1, d)
}

function daysUntil(dateStr: string): number {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const target = parseDate(dateStr)
  return Math.round((target.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))
}

function formatDate(dateStr: string): string {
  const d = parseDate(dateStr)
  return d.toLocaleDateString("en-CA", { month: "long", day: "numeric", year: "numeric" })
}

function UrgencyBadge({ days }: { days: number }) {
  if (days < 0) return <span className="text-[10px] text-muted-foreground/40">Passed</span>
  if (days === 0) return <span className="text-[10px] font-bold text-red-500">Today</span>
  if (days === 1) return <span className="text-[10px] font-bold text-red-500">Tomorrow</span>
  if (days <= 7)  return <span className="text-[10px] font-semibold text-red-500">{days} days</span>
  if (days <= 30) return <span className="text-[10px] font-semibold text-amber-500">{days} days</span>
  return <span className="text-[10px] text-muted-foreground/60">{days} days</span>
}

function UrgencyDot({ days }: { days: number }) {
  if (days < 0)   return <span className="size-2 rounded-full bg-muted-foreground/20 shrink-0" />
  if (days <= 7)  return <span className="size-2 rounded-full bg-red-500 shrink-0 animate-pulse" />
  if (days <= 30) return <span className="size-2 rounded-full bg-amber-500 shrink-0" />
  return <span className="size-2 rounded-full bg-emerald-500/60 shrink-0" />
}

function HeroCard({ deadline }: { deadline: Deadline & { days: number } }) {
  const cat = CATEGORY_CONFIG[deadline.category]
  const { theme } = useCampus()

  return (
    <div className={cn(
      "flex-1 min-w-0 rounded-2xl border border-border p-4 flex flex-col gap-3",
      deadline.days <= 7 ? "border-red-500/30 bg-red-500/5" : "bg-card"
    )}>
      <div className="flex items-start justify-between gap-2">
        <span className={cn("text-[10px] font-semibold uppercase tracking-widest", cat.color)}>
          {cat.label}
        </span>
        <span className={cn(
          "text-[10px] font-semibold px-2 py-0.5 rounded-full",
          deadline.days <= 7 ? "bg-red-500/15 text-red-500" :
          deadline.days <= 30 ? "bg-amber-500/15 text-amber-600" :
          "bg-secondary text-muted-foreground"
        )}>
          {deadline.days === 0 ? "Today" :
           deadline.days === 1 ? "Tomorrow" :
           `${deadline.days} days`}
        </span>
      </div>
      <p className="text-sm font-semibold text-foreground leading-snug">{deadline.title}</p>
      <p className="text-xs text-muted-foreground">{formatDate(deadline.date)}</p>
    </div>
  )
}

export function DeadlineTracker() {
  const { theme } = useCampus()
  const [activeFilter, setActiveFilter] = React.useState<"All" | Term>("All")
  const [showPast, setShowPast] = React.useState(false)
  const [activeCat, setActiveCat] = React.useState<Category | "All">("All")

  const withDays = DEADLINES.map((d) => ({ ...d, days: daysUntil(d.date) }))

  // Hero: next 3 upcoming
  const heroDeadlines = withDays
    .filter((d) => d.days >= 0)
    .sort((a, b) => a.days - b.days)
    .slice(0, 3)

  const filtered = withDays
    .filter((d) => activeFilter === "All" || d.term === activeFilter)
    .filter((d) => activeCat === "All" || d.category === activeCat)
    .filter((d) => showPast || d.days >= 0)
    .sort((a, b) => a.days - b.days)

  const grouped = TERM_ORDER.reduce<Record<Term, typeof filtered>>((acc, term) => {
    acc[term] = filtered.filter((d) => d.term === term)
    return acc
  }, {} as Record<Term, typeof filtered>)

  const pastCount = withDays.filter((d) => d.days < 0).length

  const categories: (Category | "All")[] = ["All", "registration", "withdrawal", "exams", "payment", "classes"]

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div>
        <h2 className="text-lg font-semibold mb-0.5">Academic Deadlines</h2>
        <p className="text-sm text-muted-foreground">
          Key dates for the 2025–26 and 2026–27 academic year.
        </p>
      </div>

      {/* Hero cards — next 3 upcoming */}
      {heroDeadlines.length > 0 && (
        <div className="flex flex-col gap-2">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/50">Coming up</p>
          <div className="flex gap-2 flex-wrap sm:flex-nowrap">
            {heroDeadlines.map((d) => <HeroCard key={d.id} deadline={d} />)}
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-col gap-2">
        {/* Term filter */}
        <div className="flex gap-1.5 flex-wrap">
          {(["All", ...TERM_ORDER] as const).map((term) => (
            <button
              key={term}
              onClick={() => setActiveFilter(term)}
              className={cn(
                "px-3 py-1.5 rounded-lg text-xs font-medium transition-all",
                activeFilter === term
                  ? "bg-foreground text-background"
                  : "border border-border text-muted-foreground hover:text-foreground hover:bg-secondary"
              )}
            >
              {term}
            </button>
          ))}
        </div>

        {/* Category filter */}
        <div className="flex gap-1.5 flex-wrap">
          {categories.map((cat) => {
            const config = cat !== "All" ? CATEGORY_CONFIG[cat] : null
            return (
              <button
                key={cat}
                onClick={() => setActiveCat(cat)}
                className={cn(
                  "px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all capitalize",
                  activeCat === cat
                    ? config ? `${config.bg} ${config.color} border border-current/20` : "bg-foreground text-background"
                    : "border border-border text-muted-foreground hover:text-foreground hover:bg-secondary"
                )}
              >
                {cat === "All" ? "All types" : CATEGORY_CONFIG[cat].label}
              </button>
            )
          })}
        </div>
      </div>

      {/* Deadline list */}
      <div className="space-y-6">
        {TERM_ORDER.map((term) => {
          const items = grouped[term]
          if (!items.length && activeFilter !== "All" && activeFilter !== term) return null
          if (!items.length) return null

          return (
            <div key={term}>
              <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/50 mb-2">
                {term}
              </p>
              <div className="rounded-xl border border-border overflow-hidden">
                {items.map((d, i) => {
                  const cat = CATEGORY_CONFIG[d.category]
                  return (
                    <div
                      key={d.id}
                      className={cn(
                        "flex items-center gap-3 px-4 py-3 transition-colors",
                        i < items.length - 1 && "border-b border-border/40",
                        d.days < 0 ? "opacity-40" : "hover:bg-secondary/30",
                        d.days >= 0 && d.days <= 7 && "bg-red-500/5"
                      )}
                    >
                      <UrgencyDot days={d.days} />

                      <div className="flex-1 min-w-0">
                        <p className={cn(
                          "text-sm font-medium truncate",
                          d.days < 0 ? "text-muted-foreground" : "text-foreground"
                        )}>
                          {d.title}
                        </p>
                        <p className="text-xs text-muted-foreground/60 mt-0.5">{formatDate(d.date)}</p>
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        <span className={cn("text-[10px] font-medium px-1.5 py-0.5 rounded-md", cat.bg, cat.color)}>
                          {cat.label}
                        </span>
                        <UrgencyBadge days={d.days} />
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>

      {/* Show past toggle */}
      <button
        onClick={() => setShowPast(!showPast)}
        className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground transition-colors mx-auto"
      >
        {showPast ? <ChevronUp className="size-3.5" /> : <ChevronDown className="size-3.5" />}
        {showPast ? "Hide" : "Show"} past deadlines ({pastCount})
      </button>
    </div>
  )
}
