"use client"

import * as React from "react"
import { GitBranch, BarChart2, GraduationCap, MessageSquare, ArrowRight } from "lucide-react"
import { useCampus, campusThemes } from "./campus-context"
import { cn } from "@/lib/utils"

interface EmptyStateProps {
  onSuggestionClick: (suggestion: string) => void
  onViewChange?: (view: string) => void
}

const TYPEWRITER_QUERIES = [
  "What are the prerequisites for SYSC 3110?",
  "What courses do I need for Software Engineering?",
  "How many credits to graduate from Computer Science?",
  "What is COMP 2804 about?",
  "Can I take SYSC 4906 without SYSC 4101?",
  "What electives are available in third year?",
]

const TOOLS = [
  {
    icon: MessageSquare,
    title: "Ask anything",
    description: "Courses, policies, prerequisites, graduation requirements.",
    action: "chat" as const,
  },
  {
    icon: GraduationCap,
    title: "Degree Planner",
    description: "Drag-and-drop your 4-year course schedule.",
    action: "planner" as const,
  },
  {
    icon: GitBranch,
    title: "Prereq Tree",
    description: "See the full prerequisite chain for any course.",
    action: "prereq" as const,
  },
  {
    icon: BarChart2,
    title: "Compare Courses",
    description: "Side-by-side comparison of up to 3 courses.",
    action: "compare" as const,
  },
]

const QUICK_ASKS = [
  "What is SYSC 3110 about?",
  "Prerequisites for COMP 3000?",
  "How many credits to graduate?",
]

function useTypewriter(strings: string[], typingSpeed = 45, pauseDuration = 2200, deletingSpeed = 20) {
  const [displayed, setDisplayed] = React.useState("")
  const [index, setIndex] = React.useState(0)
  const [phase, setPhase] = React.useState<"typing" | "pausing" | "deleting">("typing")

  React.useEffect(() => {
    const current = strings[index]

    if (phase === "typing") {
      if (displayed.length < current.length) {
        const t = setTimeout(() => setDisplayed(current.slice(0, displayed.length + 1)), typingSpeed)
        return () => clearTimeout(t)
      } else {
        const t = setTimeout(() => setPhase("pausing"), pauseDuration)
        return () => clearTimeout(t)
      }
    }

    if (phase === "pausing") {
      const t = setTimeout(() => setPhase("deleting"), 100)
      return () => clearTimeout(t)
    }

    if (phase === "deleting") {
      if (displayed.length > 0) {
        const t = setTimeout(() => setDisplayed(displayed.slice(0, -1)), deletingSpeed)
        return () => clearTimeout(t)
      } else {
        setIndex((i) => (i + 1) % strings.length)
        setPhase("typing")
      }
    }
  }, [displayed, phase, index, strings, typingSpeed, pauseDuration, deletingSpeed])

  return displayed
}

export function EmptyState({ onSuggestionClick, onViewChange }: EmptyStateProps) {
  const { selectedCampus, theme } = useCampus()
  const campusName = campusThemes[selectedCampus].name
  const typewriterText = useTypewriter(TYPEWRITER_QUERIES)

  const handleToolClick = (action: string) => {
    if (action === "chat") return
    if (action === "prereq") {
      onSuggestionClick("What are the prerequisites for SYSC 3110?")
    } else if (onViewChange) {
      onViewChange(action)
    }
  }

  return (
    <div className="flex flex-col items-center justify-center w-full min-h-full px-6 py-16">
      <div className="w-full max-w-2xl mx-auto flex flex-col items-center gap-10">

        {/* Wordmark */}
        <div className="text-center">
          <h1 className="text-5xl md:text-6xl font-bold tracking-tight text-foreground">
            Campus<span className={theme.textClass}>Q</span>
          </h1>
          <p className="mt-3 text-muted-foreground text-base">
            Academic assistant for{" "}
            <span className="text-foreground font-medium">{campusName}</span>
          </p>
        </div>

        {/* Typewriter */}
        <div className="w-full max-w-xl">
          <div className="px-5 py-4 rounded-2xl border border-border bg-card shadow-sm min-h-[56px] flex items-center">
            <span className="text-sm text-muted-foreground">
              {typewriterText}
              <span className="inline-block w-[2px] h-4 bg-muted-foreground/60 ml-[1px] align-middle animate-pulse" />
            </span>
          </div>
          <p className="text-xs text-muted-foreground/60 text-center mt-2">
            Type your question above, or explore the tools below
          </p>
        </div>

        {/* Tool grid */}
        <div className="grid grid-cols-2 gap-3 w-full">
          {TOOLS.map((tool) => {
            const Icon = tool.icon
            const isChat = tool.action === "chat"
            return (
              <button
                key={tool.title}
                onClick={() => handleToolClick(tool.action)}
                disabled={isChat}
                className={cn(
                  "group relative flex flex-col items-start gap-3 p-4 rounded-xl border text-left transition-all duration-150",
                  isChat
                    ? "border-border/40 bg-card/30 cursor-default"
                    : "border-border bg-card hover:border-foreground/20 hover:shadow-md cursor-pointer"
                )}
              >
                <div className={cn(
                  "flex items-center justify-center size-8 rounded-lg",
                  isChat ? "bg-secondary" : theme.bgClass
                )}>
                  <Icon className={cn("size-4", isChat ? "text-muted-foreground" : "text-white")} />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-foreground">{tool.title}</p>
                  <p className="text-xs text-muted-foreground leading-relaxed mt-0.5">{tool.description}</p>
                </div>
                {!isChat && (
                  <ArrowRight className="absolute right-3 top-3 size-3.5 text-muted-foreground/40 transition-transform duration-150 group-hover:translate-x-0.5 group-hover:text-muted-foreground" />
                )}
              </button>
            )
          })}
        </div>

        {/* Quick asks */}
        <div className="flex flex-col items-center gap-3 w-full">
          <p className="text-xs font-medium text-muted-foreground/70 uppercase tracking-widest">
            Quick asks
          </p>
          <div className="flex flex-wrap justify-center gap-2">
            {QUICK_ASKS.map((q) => (
              <button
                key={q}
                onClick={() => onSuggestionClick(q)}
                className="px-4 py-2 rounded-full text-xs border border-border bg-card text-foreground/70 hover:text-foreground hover:border-foreground/30 hover:shadow-sm transition-all duration-150"
              >
                {q}
              </button>
            ))}
          </div>
        </div>

      </div>
    </div>
  )
}
