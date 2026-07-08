"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { CourseCard } from "../course-card"
import { PrereqVisualizer } from "../prereq-visualizer"
import type { CourseCardData } from "./types"

interface CoursePillsProps {
  cards: CourseCardData[]
  expandedPrereq: string | null
  onTogglePrereq: (code: string) => void
}

export function CoursePills({
  cards,
  expandedPrereq,
  onTogglePrereq,
}: CoursePillsProps) {
  const [expanded, setExpanded] = React.useState<string | null>(null)

  return (
    <div className="mt-3 space-y-2">
      <div className="flex flex-wrap gap-2">
        {cards.map((card) => (
          <button
            key={card.courseCode}
            onClick={() => setExpanded(
              expanded === card.courseCode ? null : card.courseCode,
            )}
            className={cn(
              "inline-flex items-center gap-1.5 px-3.5 py-2 md:py-1.5 rounded-full text-xs font-medium border transition-[background-color,border-color,transform] active:scale-[0.97]",
              expanded === card.courseCode
                ? "bg-primary/10 border-primary/30 text-primary"
                : "bg-secondary border-border text-muted-foreground hover:text-foreground hover:border-border/80",
            )}
          >
            <span className="font-mono">{card.courseCode}</span>
            <span className="text-[10px] opacity-60">
              {expanded === card.courseCode ? "▲" : "▼"}
            </span>
          </button>
        ))}
      </div>
      {cards.map((card) => (
        expanded === card.courseCode ? (
          <div key={card.courseCode} className="space-y-2">
            <CourseCard {...card} />
            {card.prerequisites.length > 0 && (
              <button
                onClick={() => onTogglePrereq(card.courseCode)}
                className="text-xs text-primary hover:underline"
              >
                {expandedPrereq === card.courseCode
                  ? "Hide prerequisite tree"
                  : "View full prerequisite tree →"}
              </button>
            )}
            {expandedPrereq === card.courseCode && (
              <PrereqVisualizer courseCode={card.courseCode} />
            )}
          </div>
        ) : null
      ))}
    </div>
  )
}
