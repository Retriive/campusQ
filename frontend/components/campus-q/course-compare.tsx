"use client"

import * as React from "react"
import { X, Search, Plus, BarChart2, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { API_BASE_URL } from "@/lib/api"

interface CourseData {
  courseCode: string
  courseName: string
  credits: number
  description: string
  prerequisites: string[]
  prerequisiteText?: string
}

const ACCENTS = [
  { top: "bg-blue-500",    text: "text-blue-600 dark:text-blue-400",    bg: "bg-blue-50 dark:bg-blue-950/30" },
  { top: "bg-primary",     text: "text-primary",                        bg: "bg-primary-soft" },
  { top: "bg-emerald-500", text: "text-emerald-600 dark:text-emerald-400", bg: "bg-emerald-50 dark:bg-emerald-950/30" },
]

export function CourseCompare({ initialCourses = [] }: { initialCourses?: CourseData[] }) {
  const [courses, setCourses] = React.useState<CourseData[]>(initialCourses.slice(0, 3))
  const [search, setSearch] = React.useState("")
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState("")

  const addCourse = async () => {
    const code = search.trim().toUpperCase()
    if (!code || courses.length >= 3) return
    if (courses.find((c) => c.courseCode === code)) { setError("Already added."); return }
    setLoading(true); setError("")
    try {
      const res = await fetch(`${API_BASE_URL}/api/course/${encodeURIComponent(code)}`)
      const data = await res.json()
      if (data.found === false || data.error) {
        setError(`${code} not found.`)
      } else {
        setCourses(prev => [...prev, {
          courseCode: data.courseCode || code,
          courseName: data.courseName || "Unknown",
          credits: data.credits || 0.5,
          description: data.description || "",
          prerequisites: data.prerequisites || [],
          prerequisiteText: data.prerequisiteText || "",
        }])
        setSearch("")
      }
    } catch { setError("Failed to fetch. Is the backend running?") }
    finally { setLoading(false) }
  }

  const removeCourse = (code: string) => setCourses(prev => prev.filter(c => c.courseCode !== code))

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h2 className="text-lg font-semibold mb-0.5">Compare Courses</h2>
        <p className="text-sm text-muted-foreground">Add up to 3 courses to compare side by side.</p>
      </div>

      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-3.5 text-muted-foreground" />
          <input
            value={search}
            onChange={e => { setSearch(e.target.value); setError("") }}
            onKeyDown={e => e.key === "Enter" && addCourse()}
            placeholder="Enter course code (e.g. SYSC 3110)"
            className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-border bg-card text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 placeholder:text-muted-foreground/40"
          />
        </div>
        <Button onClick={addCourse} disabled={!search.trim() || courses.length >= 3 || loading} className="gap-2 rounded-xl">
          {loading ? <Loader2 className="size-4 animate-spin" /> : <Plus className="size-4" />}
          Add
        </Button>
      </div>

      {error && <p className="text-xs text-destructive">{error}</p>}

      {courses.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-14 text-muted-foreground">
          <BarChart2 className="size-9 opacity-20" />
          <p className="text-sm">Add courses above to start comparing.</p>
        </div>
      ) : (
        <div className="rounded-2xl border border-border overflow-hidden">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr>
                {/* Empty top-left cell */}
                <th className="w-28 bg-secondary/30 border-b border-border" />

                {courses.map((c, i) => {
                  const a = ACCENTS[i]
                  return (
                    <th key={c.courseCode} className={cn("text-left border-b border-border", a.bg)}>
                      {/* Colored top stripe */}
                      <div className={cn("h-1 w-full", a.top)} />
                      <div className="px-4 py-3 flex items-start justify-between gap-2">
                        <div>
                          <p className={cn("text-xs font-bold font-mono", a.text)}>{c.courseCode}</p>
                          <p className="text-sm font-semibold text-foreground leading-snug mt-0.5">{c.courseName}</p>
                        </div>
                        <button onClick={() => removeCourse(c.courseCode)} className="text-muted-foreground/30 hover:text-muted-foreground transition-colors mt-0.5 shrink-0">
                          <X className="size-3.5" />
                        </button>
                      </div>
                    </th>
                  )
                })}

                {courses.length < 3 && (
                  <th className="text-xs text-muted-foreground/30 font-normal text-center border-b border-border px-4 bg-secondary/10">
                    + add another
                  </th>
                )}
              </tr>
            </thead>

            <tbody>
              {[
                {
                  label: "Credits",
                  render: (c: CourseData) => (
                    <span className="inline-flex px-2 py-0.5 rounded-md bg-secondary text-xs font-medium text-foreground">
                      {c.credits} {c.credits === 1 ? "credit" : "credits"}
                    </span>
                  ),
                },
                {
                  label: "Prerequisites",
                  render: (c: CourseData) =>
                    c.prerequisiteText && c.prerequisiteText !== "None" ? (
                      <span className="text-xs text-muted-foreground leading-relaxed">{c.prerequisiteText}</span>
                    ) : (
                      <span className="text-xs text-muted-foreground/40 italic">None required</span>
                    ),
                },
                {
                  label: "Description",
                  render: (c: CourseData) => (
                    <span className="text-xs text-muted-foreground leading-relaxed">{c.description}</span>
                  ),
                },
              ].map((row, rowIdx, arr) => (
                <tr key={row.label} className={rowIdx % 2 === 0 ? "bg-background" : "bg-secondary/20"}>
                  <td className={cn(
                    "px-4 py-3 align-top border-r border-border",
                    rowIdx < arr.length - 1 && "border-b border-border/50"
                  )}>
                    <span className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60">
                      {row.label}
                    </span>
                  </td>

                  {courses.map((c, i) => (
                    <td
                      key={c.courseCode}
                      className={cn(
                        "px-4 py-3 align-top",
                        rowIdx < arr.length - 1 && "border-b border-border/50",
                        i < courses.length - 1 && "border-r border-border/30"
                      )}
                    >
                      {row.render(c)}
                    </td>
                  ))}

                  {courses.length < 3 && (
                    <td className={cn(
                      "px-4 py-3 bg-secondary/10",
                      rowIdx < arr.length - 1 && "border-b border-border/50"
                    )} />
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
