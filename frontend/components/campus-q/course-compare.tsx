"use client"

import * as React from "react"
import { X, Search, Plus, BarChart2, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface CourseData {
  courseCode: string
  courseName: string
  credits: number
  description: string
  prerequisites: string[]
  prerequisiteText?: string
}

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
      setError("Course already in comparison.")
      return
    }
    setLoading(true)
    setError("")
    try {
      const res = await fetch(`${API_URL}/api/course/${encodeURIComponent(code)}`)
      const data = await res.json()
      if (data.found === false || data.error) {
        setError(`Course ${code} not found in the database.`)
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
      setError("Failed to fetch course data. Is the backend running?")
    } finally {
      setLoading(false)
    }
  }

  const removeCourse = (code: string) => {
    setCourses((prev) => prev.filter((c) => c.courseCode !== code))
  }

  const rows: { label: string; key: keyof CourseData; render?: (v: CourseData) => React.ReactNode }[] = [
    { label: "Course Code", key: "courseCode" },
    { label: "Course Name", key: "courseName" },
    { label: "Credits", key: "credits", render: (c) => `${c.credits} credit unit${c.credits !== 1 ? "s" : ""}` },
    {
      label: "Prerequisites",
      key: "prerequisites",
      render: (c) =>
        c.prerequisiteText && c.prerequisiteText !== "None" ? (
          <span className="text-xs text-muted-foreground leading-relaxed">{c.prerequisiteText}</span>
        ) : (
          <span className="text-xs text-muted-foreground/50 italic">None required</span>
        ),
    },
    {
      label: "Description",
      key: "description",
      render: (c) => <p className="text-xs leading-relaxed text-muted-foreground">{c.description}</p>,
    },
  ]

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-xl font-bold mb-1">Compare Courses</h2>
        <p className="text-sm text-muted-foreground">Add up to 3 courses to compare side by side.</p>
      </div>

      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
          <input
            type="text"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setError("") }}
            onKeyDown={(e) => e.key === "Enter" && addCourse()}
            placeholder="Enter course code (e.g. SYSC 3110)"
            className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
          />
        </div>
        <Button onClick={addCourse} disabled={!search.trim() || courses.length >= 3 || loading} className="gap-2 rounded-xl">
          {loading ? <Loader2 className="size-4 animate-spin" /> : <Plus className="size-4" />}
          Add
        </Button>
      </div>

      {error && <p className="text-sm text-red-500">{error}</p>}

      {courses.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-16 text-center text-muted-foreground">
          <BarChart2 className="size-10 opacity-30" />
          <p className="text-sm">Add courses above to start comparing.</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-border">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-secondary/40">
                <th className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground w-32">
                  Field
                </th>
                {courses.map((c) => (
                  <th key={c.courseCode} className="text-left px-4 py-3">
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-mono font-bold text-foreground">{c.courseCode}</span>
                      <button
                        onClick={() => removeCourse(c.courseCode)}
                        className="text-muted-foreground hover:text-red-500 transition-colors"
                      >
                        <X className="size-4" />
                      </button>
                    </div>
                  </th>
                ))}
                {courses.length < 3 && (
                  <th className="px-4 py-3 text-muted-foreground/40 text-xs italic font-normal">
                    + add another
                  </th>
                )}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => (
                <tr key={row.label} className={i % 2 === 0 ? "bg-background" : "bg-secondary/20"}>
                  <td className="px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    {row.label}
                  </td>
                  {courses.map((c) => (
                    <td key={c.courseCode} className="px-4 py-3 align-top">
                      {row.render ? row.render(c) : <span>{String(c[row.key])}</span>}
                    </td>
                  ))}
                  {courses.length < 3 && <td />}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
