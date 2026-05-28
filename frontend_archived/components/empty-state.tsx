"use client"

import { Sparkles, Bus, Building, FileQuestion, GraduationCap } from "lucide-react"

interface SuggestionCard {
  icon: React.ReactNode
  title: string
  description: string
  gradient: string
  iconColor: string
}

interface EmptyStateProps {
  onSuggestionClick: (suggestion: string) => void
}

const suggestions: SuggestionCard[] = [
  {
    icon: <Bus className="h-5 w-5" />,
    title: "Student transportation policy",
    description: "Bus routes, eligibility, and safety rules",
    gradient: "from-amber-500/20 to-orange-500/20",
    iconColor: "text-amber-600",
  },
  {
    icon: <Building className="h-5 w-5" />,
    title: "How to rent a school gym",
    description: "Facility booking process and rates",
    gradient: "from-rose-500/20 to-pink-500/20",
    iconColor: "text-rose-500",
  },
  {
    icon: <FileQuestion className="h-5 w-5" />,
    title: "Assessment and evaluation",
    description: "Grading policies and standards",
    gradient: "from-emerald-500/20 to-teal-500/20",
    iconColor: "text-emerald-600",
  },
  {
    icon: <GraduationCap className="h-5 w-5" />,
    title: "Graduation requirements",
    description: "Credits, courses, and diplomas",
    gradient: "from-violet-500/20 to-purple-500/20",
    iconColor: "text-violet-500",
  },
]

export function EmptyState({ onSuggestionClick }: EmptyStateProps) {
  return (
    <div className="flex min-h-[calc(100vh-120px)] flex-col items-center justify-center px-4">
      {/* AI Icon with warm glow */}
      <div className="relative mb-10">
        <div className="absolute -inset-10 rounded-full bg-gradient-to-br from-primary/30 via-accent/20 to-transparent blur-3xl" />
        <div className="relative flex h-24 w-24 items-center justify-center rounded-3xl bg-gradient-to-br from-primary to-accent shadow-2xl shadow-primary/30">
          <Sparkles className="h-12 w-12 text-primary-foreground" />
        </div>
      </div>

      {/* Header */}
      <h1 className="mb-3 text-center text-3xl font-bold tracking-tight text-foreground">
        What do you need to know?
      </h1>
      <p className="mb-12 max-w-lg text-center text-[15px] leading-relaxed text-muted-foreground">
        Ask questions about OCDSB policies, procedures, and guidelines. I&apos;ll search through the knowledge base to find accurate answers.
      </p>

      {/* Suggestion Cards Grid */}
      <div className="grid w-full max-w-2xl grid-cols-1 gap-4 sm:grid-cols-2">
        {suggestions.map((suggestion, index) => (
          <button
            key={index}
            onClick={() => onSuggestionClick(suggestion.title)}
            className="group relative flex items-start gap-4 rounded-2xl border border-border bg-card p-5 text-left shadow-sm transition-all duration-300 hover:-translate-y-1 hover:border-primary/40 hover:shadow-xl hover:shadow-primary/10"
          >
            <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br ${suggestion.gradient} ${suggestion.iconColor} shadow-sm transition-all duration-300 group-hover:shadow-md`}>
              {suggestion.icon}
            </div>
            <div className="min-w-0 flex-1">
              <p className="font-semibold text-foreground">{suggestion.title}</p>
              <p className="mt-1 text-sm text-muted-foreground">
                {suggestion.description}
              </p>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
