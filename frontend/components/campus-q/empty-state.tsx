"use client"

import { BarChart2, BookOpen, CalendarDays, GitBranch, ShieldAlert, GraduationCap, Lightbulb } from "lucide-react"
import { useCampus, campusThemes } from "./campus-context"
import { cn } from "@/lib/utils"

interface EmptyStateProps {
  onSuggestionClick: (suggestion: string) => void
  onViewChange?: (view: string) => void
}

const QUICK_ASKS = [
  {
    icon: GitBranch,
    label: "Compare programs",
    question: "What's the difference between software eng and CS at Carleton?",
  },
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
  {
    icon: Lightbulb,
    label: "Course advice",
    question: "Is COMP 1405 or COMP 1005 better to start with?",
  },
]

export function EmptyState({ onSuggestionClick, onViewChange }: EmptyStateProps) {
  const { selectedCampus, theme } = useCampus()
  const campusName = campusThemes[selectedCampus].name

  return (
    <div className="flex flex-col items-center w-full px-4 pt-10 md:pt-16 pb-6 gap-8 md:gap-10">

      {/* Wordmark */}
      <div className="text-center select-none">
        <div className="inline-flex items-start gap-2">
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-foreground leading-none">
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

      {/* Tool cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 w-full max-w-2xl">
        {[
          {
            icon: BookOpen,
            label: "Programs",
            sub: "Browse degree requirements",
            action: "programs",
          },
          {
            icon: BarChart2,
            label: "Compare",
            sub: "Side-by-side course comparison",
            action: "compare",
          },
          {
            icon: CalendarDays,
            label: "Deadlines",
            sub: "Key dates with countdowns",
            action: "deadlines",
          },
        ].map((item) => {
          const Icon = item.icon
          return (
            <button
              key={item.label}
              onClick={() => onViewChange?.(item.action)}
              className="group flex flex-col gap-3 p-4 rounded-2xl border border-border bg-card hover:bg-secondary/40 hover:border-border/80 transition-all duration-150 text-left"
            >
              <div className={cn(
                "size-8 rounded-lg flex items-center justify-center",
                theme.bgClass
              )}>
                <Icon className="size-4 text-white" />
              </div>
              <div>
                <p className="text-sm font-semibold text-foreground">{item.label}</p>
                <p className="text-xs text-muted-foreground leading-relaxed mt-0.5">{item.sub}</p>
              </div>
            </button>
          )
        })}
      </div>

      {/* Quick asks */}
      <div className="flex flex-col items-center gap-3 w-full max-w-2xl">
        <p className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground/40">
          Try asking
        </p>
        <div className="grid grid-cols-2 gap-2.5 w-full">
          {QUICK_ASKS.map(({ icon: Icon, label, question }) => (
            <button
              key={label}
              onClick={() => onSuggestionClick(question)}
              className="flex items-center gap-3 px-4 py-3 rounded-xl border border-border bg-card hover:bg-secondary/40 hover:border-border/80 transition-all duration-150 text-left group"
            >
              <div className={cn("size-7 rounded-lg flex items-center justify-center shrink-0 bg-secondary group-hover:bg-secondary/80 transition-colors")}>
                <Icon className="size-3.5 text-muted-foreground" />
              </div>
              <div className="min-w-0">
                <p className="text-xs font-semibold text-foreground">{label}</p>
                <p className="text-[11px] text-muted-foreground truncate mt-0.5">{question}</p>
              </div>
            </button>
          ))}
        </div>
      </div>

    </div>
  )
}
