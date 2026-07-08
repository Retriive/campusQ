"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { useCampus } from "./campus-context"
import { CalendarDays, Clock, ChevronDown, ChevronUp, CalendarPlus, CalendarClock, X } from "lucide-react"
import { CalendarSubscribeModal, trackCalendar } from "./calendar-subscribe"

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
  { id: "fa26-timetickets",       title: "Time tickets available in Carleton Central",        date: "2026-06-17", term: "Summer 2026", category: "registration" },
  { id: "fa26-reg-new",           title: "Registration opens — new first-year students",      date: "2026-07-06", term: "Summer 2026", category: "registration" },
  { id: "fa26-reg-returning",     title: "Registration opens — returning students",           date: "2026-07-10", term: "Summer 2026", category: "registration" },
  { id: "fa26-reg-special",       title: "Registration opens — special/visiting students",    date: "2026-08-05", term: "Summer 2026", category: "registration" },
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
  payment:      { label: "Payment",      color: "text-destructive dark:text-destructive",      bg: "bg-destructive/10"    },
  classes:      { label: "Classes",      color: "text-success", bg: "bg-success/10" },
  holiday:      { label: "Holiday",      color: "text-muted-foreground",               bg: "bg-secondary"     },
}

const TERM_ORDER: Term[] = ["Summer 2026", "Fall 2026", "Winter 2027"]

// Build the chat question from the SPECIFIC deadline so it's always relevant
// (a time ticket and an add deadline are both "registration" but very different).
function askQuestion(d: Deadline): string {
  return `At Carleton, what does this academic deadline mean and what should I know about it: "${d.title}"? What happens if I miss it?`
}

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

// Categories that carry real consequences (money / grades) — the ones that matter most.
const CRITICAL_CATEGORIES: Category[] = ["registration", "withdrawal", "payment", "exams"]

// Smart default: the term that "today" falls in, or the next upcoming term.
function defaultTerm(deadlines: { term: Term; days: number }[]): Term {
  for (const term of TERM_ORDER) {
    if (deadlines.some((d) => d.term === term && d.days >= 0)) return term
  }
  return TERM_ORDER[TERM_ORDER.length - 1]
}

function icsDate(dateStr: string): string {
  return dateStr.replace(/-/g, "")  // YYYYMMDD all-day format
}

function buildICS(events: { id: string; title: string; date: string }[]): string {
  // DTSTAMP — required by RFC 5545; UTC form YYYYMMDDTHHMMSSZ
  const stamp = new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "")
  const lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//CampusQ//Academic Deadlines//EN",
    "CALSCALE:GREGORIAN",
  ]
  for (const e of events) {
    const start = icsDate(e.date)
    // all-day event; DTEND is next day per ICS spec
    const end = icsDate(
      new Date(parseDate(e.date).getTime() + 86400000).toISOString().slice(0, 10)
    )
    lines.push(
      "BEGIN:VEVENT",
      `UID:campusq-${e.id}@try-campusq`,
      `DTSTAMP:${stamp}`,
      `DTSTART;VALUE=DATE:${start}`,
      `DTEND;VALUE=DATE:${end}`,
      `SUMMARY:${e.title}`,
      "DESCRIPTION:Carleton academic deadline (via CampusQ). Verify at carleton.ca.",
      "BEGIN:VALARM",
      "TRIGGER:-P2D",
      "ACTION:DISPLAY",
      `DESCRIPTION:Reminder: ${e.title} in 2 days`,
      "END:VALARM",
      "END:VEVENT",
    )
  }
  lines.push("END:VCALENDAR")
  return lines.join("\r\n")
}

function downloadICS(events: { id: string; title: string; date: string }[], filename: string) {
  const blob = new Blob([buildICS(events)], { type: "text/calendar;charset=utf-8" })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

function googleCalUrl(title: string, dateStr: string): string {
  const start = icsDate(dateStr)
  const end = icsDate(new Date(parseDate(dateStr).getTime() + 86400000).toISOString().slice(0, 10))
  const params = new URLSearchParams({
    action: "TEMPLATE",
    text: title,
    dates: `${start}/${end}`,
    details: "Carleton academic deadline (via CampusQ). Verify at carleton.ca.",
  })
  return `https://calendar.google.com/calendar/render?${params.toString()}`
}

// Works for both school (M365) and personal accounts — outlook.office.com
// redirects personal users to outlook.live.com with the params intact.
function outlookCalUrl(title: string, dateStr: string): string {
  const end = new Date(parseDate(dateStr).getTime() + 86400000).toISOString().slice(0, 10)
  const params = new URLSearchParams({
    rru: "addevent",
    path: "/calendar/action/compose",
    allday: "true",
    subject: title,
    startdt: dateStr,
    enddt: end,
    body: "Carleton academic deadline (via CampusQ). Verify at carleton.ca.",
  })
  return `https://outlook.office.com/calendar/0/action/compose?${params.toString()}`
}

// One consistent pair of quick-add links, used in the modal / countdown / rows.
function AddToCalendarLinks({ deadline, compact }: { deadline: Deadline; compact?: boolean }) {
  const { theme } = useCampus()
  const linkClass = (primary: boolean) =>
    cn(
      "inline-flex items-center gap-1.5 text-xs font-medium rounded-lg transition-opacity",
      compact ? "px-2.5 py-1.5" : "px-3 py-2",
      primary
        ? cn("text-white hover:opacity-90", theme.bgClass)
        : "border border-border text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
    )
  return (
    <>
      <a
        href={googleCalUrl(deadline.title, deadline.date)}
        target="_blank" rel="noopener noreferrer"
        onClick={() => trackCalendar("google", "add_event", deadline.id)}
        className={linkClass(true)}
      >
        <CalendarPlus className={compact ? "size-3" : "size-3.5"} /> Google
      </a>
      <a
        href={outlookCalUrl(deadline.title, deadline.date)}
        target="_blank" rel="noopener noreferrer"
        onClick={() => trackCalendar("outlook", "add_event", deadline.id)}
        className={linkClass(false)}
      >
        <CalendarPlus className={compact ? "size-3" : "size-3.5"} /> Outlook
      </a>
    </>
  )
}

function UrgencyBadge({ days }: { days: number }) {
  if (days < 0) return <span className="text-[10px] text-muted-foreground/40">Passed</span>
  if (days === 0) return <span className="text-[10px] font-bold text-destructive">Today</span>
  if (days === 1) return <span className="text-[10px] font-bold text-destructive">Tomorrow</span>
  if (days <= 7)  return <span className="text-[10px] font-semibold text-destructive">{days} days</span>
  if (days <= 30) return <span className="text-[10px] font-semibold text-warning">{days} days</span>
  return <span className="text-[10px] text-muted-foreground/60">{days} days</span>
}

function UrgencyDot({ days }: { days: number }) {
  if (days < 0)   return <span className="size-2 rounded-full bg-muted-foreground/20 shrink-0" />
  if (days <= 7)  return <span className="size-2 rounded-full bg-destructive shrink-0 animate-pulse" />
  if (days <= 30) return <span className="size-2 rounded-full bg-warning shrink-0" />
  return <span className="size-2 rounded-full bg-success/60 shrink-0" />
}

function HeroCard({ deadline, onClick }: { deadline: Deadline & { days: number }; onClick: () => void }) {
  const cat = CATEGORY_CONFIG[deadline.category]
  const { theme } = useCampus()

  return (
    <button
      onClick={onClick}
      className={cn(
        "flex-1 min-w-0 rounded-2xl border border-border p-4 flex flex-col gap-3 text-left hover:border-border/80 hover:shadow-sm transition-[border-color,box-shadow,transform] duration-200 ease-[var(--ease-out)] active:scale-[0.98]",
        deadline.days <= 7 ? "border-destructive/30 bg-destructive/5" : "bg-card"
      )}>
      <span className={cn("text-[10px] font-semibold uppercase tracking-widest", cat.color)}>
        {cat.label}
      </span>
      <p className="text-sm font-semibold text-foreground leading-snug">{deadline.title}</p>
      <p className="text-xs text-muted-foreground">{formatDate(deadline.date)}</p>
    </button>
  )
}

// ── Detail modal (for hero cards) ─────────────────────────────────────────────
function DeadlineModal({
  deadline, onClose, onAsk,
}: {
  deadline: Deadline & { days: number }
  onClose: () => void
  onAsk?: (q: string) => void
}) {
  const { theme } = useCampus()
  const cat = CATEGORY_CONFIG[deadline.category]

  // close on Escape
  React.useEffect(() => {
    const h = (e: KeyboardEvent) => { if (e.key === "Escape") onClose() }
    window.addEventListener("keydown", h)
    return () => window.removeEventListener("keydown", h)
  }, [onClose])

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-in fade-in duration-150"
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-md rounded-2xl border border-border bg-card shadow-2xl overflow-hidden animate-in zoom-in-95 duration-150"
      >
        {/* Header */}
        <div className="p-5 border-b border-border/50">
          <div className="flex items-start justify-between gap-3">
            <span className={cn("text-[10px] font-semibold uppercase tracking-widest", cat.color)}>{cat.label}</span>
            <button onClick={onClose} className="text-muted-foreground/40 hover:text-foreground transition-colors">
              <X className="size-4" />
            </button>
          </div>
          <div className="flex items-center gap-3 mt-3">
            <div className={cn(
              "flex flex-col items-center justify-center rounded-xl px-3.5 py-2 shrink-0",
              deadline.days <= 7 ? "bg-destructive text-white" : "bg-secondary text-foreground"
            )}>
              <span className="text-xl font-bold leading-none tabular-nums">
                {deadline.days === 0 ? "!" : deadline.days}
              </span>
              <span className="text-[9px] uppercase tracking-wider mt-0.5">
                {deadline.days === 0 ? "today" : deadline.days === 1 ? "day" : "days"}
              </span>
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-foreground leading-snug">{deadline.title}</p>
              <p className="text-xs text-muted-foreground mt-0.5">{formatDate(deadline.date)}</p>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="p-5">
          <div className="flex flex-wrap gap-2">
            <AddToCalendarLinks deadline={deadline} />
            {onAsk && (
              <button
                onClick={() => { onAsk(askQuestion(deadline)); onClose() }}
                className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-2 rounded-lg border border-border text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
              >
                Ask CampusQ about this →
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export function DeadlineTracker({ onAsk }: { onAsk?: (question: string) => void }) {
  const { theme } = useCampus()
  const withDays = DEADLINES.map((d) => ({ ...d, days: daysUntil(d.date) }))

  // Smart default — open on the current/next term, not "All"
  const [activeFilter, setActiveFilter] = React.useState<"All" | Term>(() => defaultTerm(withDays))
  const [showPast, setShowPast] = React.useState(false)
  const [activeCat, setActiveCat] = React.useState<Category | "All">("All")
  const [expandedId, setExpandedId] = React.useState<string | null>(null)
  const [modalId, setModalId] = React.useState<string | null>(null)
  const [showSubscribe, setShowSubscribe] = React.useState(false)
  const modalDeadline = withDays.find((d) => d.id === modalId) || null

  // The single most urgent CRITICAL deadline — the big countdown
  const nextCritical = withDays
    .filter((d) => d.days >= 0 && CRITICAL_CATEGORIES.includes(d.category))
    .sort((a, b) => a.days - b.days)[0]

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
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold mb-0.5">Academic Deadlines</h2>
          <p className="text-sm text-muted-foreground">
            Key dates for the 2025–26 and 2026–27 academic year.
          </p>
        </div>
        <div className="shrink-0 flex gap-1.5">
          <button
            onClick={() => setShowSubscribe(true)}
            className={cn("inline-flex items-center gap-1.5 text-xs font-medium px-3 py-2 rounded-lg text-white transition-opacity hover:opacity-90", theme.bgClass)}
            title="Subscribe in Google/Outlook/Apple — updates automatically"
          >
            <CalendarClock className="size-3.5" /> Sync<span className="hidden sm:inline"> to calendar</span>
          </button>
          <button
            onClick={() => {
              trackCalendar("ics", "download_all")
              downloadICS(
                withDays.filter((d) => d.days >= 0).map((d) => ({ id: d.id, title: d.title, date: d.date })),
                "campusq-deadlines.ics"
              )
            }}
            className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-2 rounded-lg border border-border text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
            title="One-time download of all upcoming deadlines (.ics)"
          >
            <CalendarPlus className="size-3.5" /> <span className="hidden sm:inline">Download</span>.ics
          </button>
        </div>
      </div>

      {/* Big countdown — next critical deadline */}
      {nextCritical && (
        <div className={cn(
          "rounded-2xl border p-4 flex items-center gap-4",
          nextCritical.days <= 7 ? "border-destructive/40 bg-destructive/10" : "border-border bg-card"
        )}>
          <div className={cn(
            "flex flex-col items-center justify-center rounded-xl px-4 py-2 shrink-0",
            nextCritical.days <= 7 ? "bg-destructive text-white" : "bg-secondary text-foreground"
          )}>
            <span className="text-2xl font-bold leading-none tabular-nums">
              {nextCritical.days === 0 ? "!" : nextCritical.days}
            </span>
            <span className="text-[9px] uppercase tracking-wider mt-0.5">
              {nextCritical.days === 0 ? "today" : nextCritical.days === 1 ? "day" : "days"}
            </span>
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60 mb-0.5">Next critical deadline</p>
            <p className="text-sm font-semibold text-foreground leading-snug">{nextCritical.title}</p>
            <p className="text-xs text-muted-foreground mt-0.5">{formatDate(nextCritical.date)}</p>
          </div>
          <a
            href={googleCalUrl(nextCritical.title, nextCritical.date)}
            target="_blank" rel="noopener noreferrer"
            title="Add to calendar"
            onClick={() => trackCalendar("google", "add_event", nextCritical.id)}
            className="shrink-0 inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-2 rounded-lg border border-border hover:bg-secondary transition-colors"
          >
            <CalendarPlus className="size-3.5" /> <span className="hidden sm:inline">Remind me</span>
          </a>
        </div>
      )}

      {/* Hero cards — next 3 upcoming */}
      {heroDeadlines.length > 0 && (
        <div className="flex flex-col gap-2">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/50">Coming up</p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
            {heroDeadlines.map((d) => <HeroCard key={d.id} deadline={d} onClick={() => setModalId(d.id)} />)}
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
                "px-3 py-1.5 rounded-lg text-xs font-medium transition-[color,background-color,border-color,transform] duration-150 ease-[var(--ease-out)] active:scale-[0.97]",
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
                  "px-2.5 py-1 rounded-lg text-[11px] font-medium transition-[color,background-color,border-color,transform] duration-150 ease-[var(--ease-out)] active:scale-[0.97] capitalize",
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
                  const open = expandedId === d.id
                  return (
                    <div key={d.id} className={cn(i < items.length - 1 && "border-b border-border/40")}>
                      {/* Row (clickable) */}
                      <button
                        onClick={() => setExpandedId(open ? null : d.id)}
                        className={cn(
                          "w-full flex items-center gap-3 px-4 py-3 transition-colors text-left",
                          d.days < 0 ? "opacity-40" : "hover:bg-secondary/30",
                          d.days >= 0 && d.days <= 7 && !open && "bg-destructive/5"
                        )}
                      >
                        <UrgencyDot days={d.days} />
                        <div className="flex-1 min-w-0">
                          <p className={cn("text-sm font-medium leading-snug", d.days < 0 ? "text-muted-foreground" : "text-foreground")}>
                            {d.title}
                          </p>
                          <p className="text-xs text-muted-foreground/60 mt-0.5">{formatDate(d.date)}</p>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          <span className={cn("text-[10px] font-medium px-1.5 py-0.5 rounded-md hidden sm:inline", cat.bg, cat.color)}>
                            {cat.label}
                          </span>
                          <UrgencyBadge days={d.days} />
                          <ChevronDown className={cn("size-3.5 text-muted-foreground/40 transition-transform", open && "rotate-180")} />
                        </div>
                      </button>

                      {/* Expanded detail */}
                      {open && (
                        <div className="px-4 pb-4 pt-1 bg-secondary/20">
                          <div className="flex flex-wrap gap-2">
                            <AddToCalendarLinks deadline={d} compact />
                            {onAsk && (
                              <button
                                onClick={() => onAsk(askQuestion(d))}
                                className="inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1.5 rounded-lg border border-border text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
                              >
                                Ask CampusQ about this →
                              </button>
                            )}
                          </div>
                        </div>
                      )}
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

      {modalDeadline && (
        <DeadlineModal deadline={modalDeadline} onClose={() => setModalId(null)} onAsk={onAsk} />
      )}
      {showSubscribe && <CalendarSubscribeModal onClose={() => setShowSubscribe(false)} />}
    </div>
  )
}
