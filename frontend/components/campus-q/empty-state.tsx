"use client"

import { BarChart2, BookOpen, CalendarDays, ShieldAlert, GraduationCap } from "lucide-react"
import { useCampus, campusThemes } from "./campus-context"
import { cn } from "@/lib/utils"

interface EmptyStateProps {
  onSuggestionClick: (suggestion: string) => void
  onViewChange?: (view: string) => void
}

const TOOLS = [
  { icon: BookOpen, label: "Programs", sub: "Browse degree requirements", action: "programs" },
  { icon: BarChart2, label: "Compare", sub: "Courses side by side", action: "compare" },
  { icon: CalendarDays, label: "Deadlines", sub: "Key dates with countdowns", action: "deadlines" },
]

const QUICK_ASKS = [
  {
    icon: ShieldAlert,
    label: "Check prereqs",
    question: "Can I take COMP 3000 without COMP 2401?",
  },
  {
    icon: GraduationCap,
    label: "Academic rules",
    question: "What happens if I fail a required course twice?",
  },
]

export function EmptyState({ onSuggestionClick, onViewChange }: EmptyStateProps) {
  const { selectedCampus, theme } = useCampus()
  const campusName = campusThemes[selectedCampus].name

  return (
    <div className="flex flex-col items-center w-full px-4 pt-6 md:pt-16 pb-4 md:pb-6 gap-6 md:gap-10">

      {/* Wordmark */}
      <div className="text-center select-none">
        <div className="inline-flex items-start gap-2">
          <h1 className="text-3xl md:text-5xl font-bold tracking-tight text-foreground leading-none">
            Campus<span className={theme.textClass}>Q</span>
          </h1>
          <span className={cn(
            "mt-1 text-[10px] font-semibold uppercase tracking-widest px-2 py-0.5 rounded-full border",
            "text-muted-foreground border-border bg-secondary/60"
          )}>
            beta
          </span>
        </div>
        <p className="mt-2 text-sm text-muted-foreground">
          AI academic assistant for <span className="text-foreground font-medium">{campusName}</span>
        </p>
      </div>

      {/* Tools — desktop only; mobile uses the bottom tab bar */}
      <div className="hidden sm:grid grid-cols-1 sm:grid-cols-3 gap-3 w-full max-w-2xl">
        {TOOLS.map((item) => {
          const Icon = item.icon
          return (
            <button
              key={item.label}
              onClick={() => onViewChange?.(item.action)}
              className="group flex items-start gap-3 p-4 rounded-xl border border-border/70 bg-card/40 hover:bg-card hover:border-border transition-[background-color,border-color,transform] duration-200 ease-[var(--ease-out)] active:scale-[0.98] text-left"
            >
              <Icon className="size-4 mt-0.5 shrink-0 text-muted-foreground group-hover:text-foreground transition-colors duration-200" />
              <div className="min-w-0">
                <p className="text-sm font-semibold text-foreground leading-tight">{item.label}</p>
                <p className="text-[11px] text-muted-foreground leading-snug mt-1">{item.sub}</p>
              </div>
            </button>
          )
        })}
      </div>

      {/* Quick asks — two prompts only */}
      <div className="flex flex-col items-center gap-2.5 md:gap-3 w-full max-w-2xl">
        <p className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground/70">
          Try asking
        </p>
        <div className="grid grid-cols-1 gap-2 w-full sm:grid-cols-2 sm:gap-2.5">
          {QUICK_ASKS.map(({ icon: Icon, label, question }) => (
            <button
              key={question}
              onClick={() => onSuggestionClick(question)}
              className="flex items-center gap-3 px-4 py-3 rounded-2xl border border-border bg-card shadow-resting hover:border-border/80 hover:shadow-raised transition-[background-color,border-color,box-shadow,transform] duration-200 ease-[var(--ease-out)] active:scale-[0.98] text-left group"
            >
              <div className={cn("size-9 sm:size-7 rounded-xl sm:rounded-lg flex items-center justify-center shrink-0 bg-secondary group-hover:bg-primary-soft transition-colors")}>
                <Icon className="size-4 sm:size-3.5 text-muted-foreground group-hover:text-primary-ink transition-colors" />
              </div>
              <div className="min-w-0">
                <p className="text-xs font-semibold text-foreground">{label}</p>
                <p className="text-[12px] sm:text-[11px] text-muted-foreground line-clamp-2 sm:truncate mt-0.5 leading-snug">
                  {question}
                </p>
              </div>
            </button>
          ))}
        </div>
      </div>

    </div>
  )
}
