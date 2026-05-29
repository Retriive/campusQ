"use client"

import { BarChart2, BookOpen } from "lucide-react"
import { useCampus, campusThemes } from "./campus-context"
import { cn } from "@/lib/utils"

interface EmptyStateProps {
  onSuggestionClick: (suggestion: string) => void
  onViewChange?: (view: string) => void
}

const QUICK_ASKS = [
  "What is SYSC 3110 about?",
  "Prerequisites for COMP 3000?",
  "Courses required for Software Engineering?",
  "How many credits to graduate?",
]

export function EmptyState({ onSuggestionClick, onViewChange }: EmptyStateProps) {
  const { selectedCampus, theme } = useCampus()
  const campusName = campusThemes[selectedCampus].name

  return (
    <div className="flex flex-col items-center w-full px-4 pt-16 pb-6 gap-10">

      {/* Wordmark */}
      <div className="text-center select-none">
        <h1 className="text-[2.75rem] md:text-5xl font-bold tracking-tight text-foreground leading-none">
          Campus<span className={theme.textClass}>Q</span>
        </h1>
        <p className="mt-2.5 text-sm text-muted-foreground">
          Your AI advisor for <span className="text-foreground font-medium">{campusName}</span>
        </p>
      </div>

      {/* Tool cards */}
      <div className="grid grid-cols-2 gap-3 w-full max-w-lg">
        {[
          {
            icon: BookOpen,
            label: "Program Explorer",
            sub: "Browse requirements for any Carleton program",
            action: "programs",
          },
          {
            icon: BarChart2,
            label: "Compare Courses",
            sub: "Side-by-side comparison of up to 3 courses",
            action: "compare",
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
      <div className="flex flex-col items-center gap-2.5 w-full max-w-lg">
        <p className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground/40">
          Try asking
        </p>
        <div className="flex flex-wrap justify-center gap-2">
          {QUICK_ASKS.map((q) => (
            <button
              key={q}
              onClick={() => onSuggestionClick(q)}
              className="px-3.5 py-1.5 rounded-full text-xs border border-border bg-card text-muted-foreground hover:text-foreground hover:border-foreground/20 hover:shadow-sm transition-all duration-150"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

    </div>
  )
}
