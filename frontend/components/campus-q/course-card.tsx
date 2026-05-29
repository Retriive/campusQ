"use client"

import { BookOpen } from "lucide-react"
import { useCampus } from "./campus-context"
import { cn } from "@/lib/utils"

interface CourseCardProps {
  courseCode: string
  courseName: string
  credits: number
  description: string
  prerequisites: string[]
  prerequisiteText?: string
}

export function CourseCard({
  courseCode,
  courseName,
  credits,
  description,
  prerequisites,
  prerequisiteText,
}: CourseCardProps) {
  const { theme } = useCampus()

  const hasChips = prerequisites.length > 0
  const hasRawText = prerequisiteText && prerequisiteText !== "None"

  return (
    <div className="w-full rounded-xl border border-border bg-card overflow-hidden shadow-sm">
      <div className={cn("h-[3px] w-full", theme.bgClass)} />

      <div className="p-5 space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className={cn("flex items-center justify-center size-9 rounded-lg shrink-0", theme.bgClass)}>
              <BookOpen className="size-4 text-white" />
            </div>
            <div>
              <p className="text-xs font-mono font-semibold text-muted-foreground tracking-wider uppercase">
                {courseCode}
              </p>
              <h3 className="text-sm font-semibold text-foreground leading-tight mt-0.5">
                {courseName}
              </h3>
            </div>
          </div>
          <span className="shrink-0 text-xs font-semibold text-muted-foreground bg-secondary px-2.5 py-1 rounded-md">
            {credits} {credits === 1 ? "credit" : "credits"}
          </span>
        </div>

        {/* Description */}
        {description && (
          <p className="text-sm text-muted-foreground leading-relaxed border-t border-border/50 pt-4">
            {description}
          </p>
        )}

        {/* Prerequisites — always show raw text to preserve OR/AND logic */}
        <div className="border-t border-border/50 pt-4">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
            Prerequisites
          </p>
          {hasRawText ? (
            <p className="text-xs text-muted-foreground leading-relaxed">{prerequisiteText}</p>
          ) : (
            <p className="text-xs text-muted-foreground/50 italic">None required.</p>
          )}
        </div>
      </div>
    </div>
  )
}
