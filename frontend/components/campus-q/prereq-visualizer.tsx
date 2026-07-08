"use client"

import * as React from "react"
import { ChevronRight, ChevronDown, GitBranch, Loader2 } from "lucide-react"
import { API_BASE_URL } from "@/lib/api"

interface CourseNode {
  courseCode: string
  courseName: string
  credits: number
  prerequisites: string[]
}

interface TreeNodeProps {
  courseCode: string
  depth?: number
  maxDepth?: number
  visited?: Set<string>
}

function TreeNode({ courseCode, depth = 0, maxDepth = 3, visited = new Set() }: TreeNodeProps) {
  const [course, setCourse] = React.useState<CourseNode | null>(null)
  const [expanded, setExpanded] = React.useState(depth < 1)
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState(false)

  const isVisited = visited.has(courseCode)
  const newVisited = new Set(visited)
  newVisited.add(courseCode)

  React.useEffect(() => {
    if (isVisited) return
    setLoading(true)
    fetch(`${API_BASE_URL}/api/course/${encodeURIComponent(courseCode)}`)
      .then((r) => r.json())
      .then((data) => {
        if (data.found !== false) {
          setCourse({
            courseCode: data.courseCode || courseCode,
            courseName: data.courseName || "Course Details",
            credits: data.credits || 0.5,
            prerequisites: data.prerequisites || [],
          })
        } else {
          setError(true)
        }
      })
      .catch(() => setError(true))
      .finally(() => setLoading(false))
  }, [courseCode, isVisited])

  const hasPrereqs = course && course.prerequisites.length > 0
  const canExpand = hasPrereqs && depth < maxDepth && !isVisited

  const colors = [
    "border-primary bg-primary/5",
    "border-blue-400 bg-blue-400/5",
    "border-purple-400 bg-purple-400/5",
    "border-orange-400 bg-orange-400/5",
  ]
  const colorClass = colors[Math.min(depth, colors.length - 1)]

  return (
    <div className={`${depth > 0 ? "ml-6 mt-2" : ""}`}>
      <div className={`flex items-start gap-2 p-2.5 rounded-lg border ${colorClass} transition-colors`}>
        {canExpand ? (
          <button
            onClick={() => setExpanded(!expanded)}
            className="mt-0.5 shrink-0 text-muted-foreground hover:text-foreground transition-colors"
          >
            {expanded ? <ChevronDown className="size-4" /> : <ChevronRight className="size-4" />}
          </button>
        ) : (
          <div className="mt-0.5 shrink-0 size-4" />
        )}

        <div className="flex-1 min-w-0">
          {loading ? (
            <div className="flex items-center gap-2 text-muted-foreground text-sm">
              <Loader2 className="size-3 animate-spin" />
              <span className="font-mono font-medium">{courseCode}</span>
            </div>
          ) : error || isVisited ? (
            <div className="text-sm">
              <span className="font-mono font-medium text-foreground">{courseCode}</span>
              {isVisited && <span className="ml-2 text-xs text-muted-foreground">(see above)</span>}
            </div>
          ) : course ? (
            <div>
              <div className="flex items-baseline gap-2 flex-wrap">
                <span className="font-mono font-semibold text-sm text-foreground">{course.courseCode}</span>
                <span className="text-xs text-muted-foreground truncate">{course.courseName}</span>
                <span className="text-xs text-muted-foreground ml-auto shrink-0">{course.credits} cr</span>
              </div>
              {!hasPrereqs && (
                <p className="text-xs text-muted-foreground mt-0.5">No prerequisites</p>
              )}
            </div>
          ) : null}
        </div>
      </div>

      {expanded && canExpand && course?.prerequisites.map((prereq) => (
        <TreeNode
          key={prereq}
          courseCode={prereq}
          depth={depth + 1}
          maxDepth={maxDepth}
          visited={newVisited}
        />
      ))}
    </div>
  )
}

interface PrereqVisualizerProps {
  courseCode: string
}

export function PrereqVisualizer({ courseCode }: PrereqVisualizerProps) {
  return (
    <div className="mt-4 border border-border rounded-xl overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 bg-secondary/30 border-b border-border">
        <GitBranch className="size-4 text-primary" />
        <span className="text-sm font-semibold">Prerequisite Chain</span>
        <span className="text-xs text-muted-foreground ml-1">— click to expand</span>
      </div>
      <div className="p-4">
        <TreeNode courseCode={courseCode} depth={0} maxDepth={4} visited={new Set()} />
      </div>
    </div>
  )
}
