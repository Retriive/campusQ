"use client"

import * as React from "react"
import { X, Search, Plus, BarChart2, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface CourseData {
  courseCode: string
  courseName: string
  credits: number
  description: string
  prerequisites: string[]
  prerequisiteText?: string
}

// One accent color per column slot
const COURSE_COLORS = [
  {
    border: "border-t-blue-500",
    badge: "bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300",
    header: "bg-blue-50/60 dark:bg-blue-950/20",
    dot: "bg-blue-500",
  },
  {
    border: "border-t-primary",
    badge: "bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-300",
    header: "bg-red-50/60 dark:bg-red-950/20",
    dot: "bg-primary",
  },
  {
    border: "border-t-emerald-500",
    badge: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300",
    header: "bg-emerald-50/60 dark:bg-emerald-950/20",
    dot: "bg-emerald-500",
  },
]

const ROWS = [
  { key: "courseCode", label: "Course Code" },
  { key: "credits", label: "Credits" },
  { key: "prerequisites", label: "Prerequisites" },
  { key: "description", label: "Description" },
] as const

interface CourseCompareProps {
  initialCourses?: CourseData[]
}

export function CourseCompare({ initialCourses = [] }: CourseCompareProps) {
  const [courses, setCourses] = React.useState<CourseData[]>(initialCourses.slice(0, 3))
  const [search, setSearch] = React.useState("")
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState("")

  const addCourse = async () => {
    const code = search.trim().toUpperCase()
    if (!code || courses.length >= 3) return
    if (courses.find((c) => c.courseCode === code)) {
      setError("Already added.")
      return
    }
    setLoading(true)
    setError("")
    try {
      const res = await fetch(`${API_URL}/api/course/${encodeURIComponent(code)}`)
      const data = await res.json()
      if (data.found === false || data.error) {
        setError(`${code} not found in the database.`)
      } else {
        setCourses((prev) => [
          ...prev,
          {
            courseCode: data.courseCode || code,
            courseName: data.courseName || "Unknown",
            credits: data.credits || 0.5,
            description: data.description || "No description available.",
            prerequisites: data.prerequisites || [],
            prerequisiteText: data.prerequisiteText || "",
          },
        ])
        setSearch("")
      }
    } catch {
      setError("Failed to fetch. Is the backend running?")
    } finally {
      setLoading(false)
    }
  }

  const removeCourse = (code: string) =>
    setCourses((prev) => prev.filter((c) => c.courseCode !== code))

  const renderCell = (course: CourseData, key: typeof ROWS[number]["key"]) => {
    switch (key) {
      case "courseCode":
        return (
          <span className="font-mono font-semibold text-sm text-foreground">
            {course.courseCode}
          </span>
        )
      case "credits":
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-secondary text-xs font-medium text-foreground">
            {course.credits} {course.credits === 1 ? "credit" : "credits"}
          </span>
        )
      case "prerequisites":
        return course.prerequisiteText && course.prerequisiteText !== "None" ? (
          <p className="text-xs text-muted-foreground leading-relaxed">
            {course.prerequisiteText}
          </p>
        ) : (
          <span className="text-xs text-muted-foreground/50 italic">None required</span>
        )
      case "description":
        return (
          <p className="text-xs text-muted-foreground leading-relaxed">
            {course.description}
          </p>
        )
    }
  }

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h2 className="text-lg font-semibold mb-0.5">Compare Courses</h2>
        <p className="text-sm text-muted-foreground">Add up to 3 courses to compare side by side.</p>
      </div>

      {/* Search input */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-3.5 text-muted-foreground" />
          <input
            type="text"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setError("") }}
            onKeyDown={(e) => e.key === "Enter" && addCourse()}
            placeholder="Enter course code (e.g. SYSC 3110)"
            className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-border bg-card text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 placeholder:text-muted-foreground/40"
          />
        </div>
        <Button
          onClick={addCourse}
          disabled={!search.trim() || courses.length >= 3 || loading}
          className="gap-2 rounded-xl"
        >
          {loading ? <Loader2 className="size-4 animate-spin" /> : <Plus className="size-4" />}
          Add
        </Button>
      </div>

      {error && <p className="text-xs text-red-500">{error}</p>}

      {courses.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-14 text-muted-foreground">
          <BarChart2 className="size-9 opacity-20" />
          <p className="text-sm">Add courses above to start comparing.</p>
        </div>
      ) : (
        <div className="grid gap-4" style={{ gridTemplateColumns: `140px repeat(${courses.length}, 1fr)` }}>

          {/* Column headers — one card per course */}
          <div /> {/* empty corner */}
          {courses.map((course, i) => {
            const color = COURSE_COLORS[i]
            return (
              <div
                key={course.courseCode}
                className={cn(
                  "relative rounded-xl border-t-2 border border-border pt-4 pb-3 px-4",
                  color.border,
                  color.header
                )}
              >
                <button
                  onClick={() => removeCourse(course.courseCode)}
                  className="absolute top-2.5 right-2.5 text-muted-foreground/40 hover:text-muted-foreground transition-colors"
                >
                  <X className="size-3.5" />
                </button>
                <span className={cn("text-[10px] font-semibold px-1.5 py-0.5 rounded-md mb-2 inline-block", color.badge)}>
                  {course.courseCode}
                </span>
                <p className="text-sm font-semibold text-foreground leading-snug pr-4">
                  {course.courseName}
                </p>
                {courses.length < 3 && i === courses.length - 1 && (
                  <p className="text-[10px] text-muted-foreground/40 mt-1">+ add another</p>
                )}
              </div>
            )
          })}

          {/* Rows */}
          {ROWS.map((row, rowIdx) => (
            <React.Fragment key={row.key}>
              {/* Row label */}
              <div className={cn(
                "flex items-start py-3 pr-3",
                rowIdx < ROWS.length - 1 && "border-b border-border/40"
              )}>
                <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/60 pt-0.5">
                  {row.label}
                </span>
              </div>

              {/* Cells */}
              {courses.map((course, i) => (
                <div
                  key={course.courseCode}
                  className={cn(
                    "py-3 px-1",
                    rowIdx < ROWS.length - 1 && "border-b border-border/40"
                  )}
                >
                  {renderCell(course, row.key)}
                </div>
              ))}

              {/* Empty placeholder column if < 3 courses */}
              {courses.length < 3 && (
                <div className={cn(
                  "py-3",
                  rowIdx < ROWS.length - 1 && "border-b border-border/40"
                )} />
              )}
            </React.Fragment>
          ))}

        </div>
      )}
    </div>
  )
}
