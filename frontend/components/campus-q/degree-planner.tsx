"use client"

import * as React from "react"
import { Plus, X, GraduationCap, Save, Trash2, RotateCcw } from "lucide-react"
import { Button } from "@/components/ui/button"

interface PlannedCourse {
  id: string
  code: string
  name: string
  credits: number
}

type SemesterPlan = PlannedCourse[]

const STORAGE_KEY = "campusq-degree-plan"
const SEMESTERS = 8

function getDefaultPlan(): SemesterPlan[] {
  return Array.from({ length: SEMESTERS }, () => [])
}

const SEMESTER_LABELS = [
  "Year 1 — Fall",
  "Year 1 — Winter",
  "Year 2 — Fall",
  "Year 2 — Winter",
  "Year 3 — Fall",
  "Year 3 — Winter",
  "Year 4 — Fall",
  "Year 4 — Winter",
]

export function DegreePlanner() {
  const [semesters, setSemesters] = React.useState<SemesterPlan[]>(getDefaultPlan)
  const [dragInfo, setDragInfo] = React.useState<{ courseId: string; fromSem: number } | null>(null)
  const [dragOverSem, setDragOverSem] = React.useState<number | null>(null)
  const [addTarget, setAddTarget] = React.useState<number | null>(null)
  const [addInput, setAddInput] = React.useState("")
  const [saved, setSaved] = React.useState(false)

  React.useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored)
        if (Array.isArray(parsed) && parsed.length === SEMESTERS) {
          setSemesters(parsed)
        }
      }
    } catch {}
  }, [])

  const savePlan = (plan: SemesterPlan[]) => {
    setSemesters(plan)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(plan))
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const addCourse = (semIndex: number) => {
    const raw = addInput.trim().toUpperCase()
    if (!raw) return
    const parts = raw.split(" ")
    const code = parts.slice(0, 2).join(" ")
    const newCourse: PlannedCourse = {
      id: `${code}-${Date.now()}`,
      code,
      name: parts.slice(2).join(" ") || "",
      credits: 0.5,
    }
    const updated = semesters.map((sem, i) => (i === semIndex ? [...sem, newCourse] : sem))
    savePlan(updated)
    setAddInput("")
    setAddTarget(null)
  }

  const removeCourse = (semIndex: number, courseId: string) => {
    const updated = semesters.map((sem, i) =>
      i === semIndex ? sem.filter((c) => c.id !== courseId) : sem
    )
    savePlan(updated)
  }

  const handleDragStart = (e: React.DragEvent, courseId: string, fromSem: number) => {
    setDragInfo({ courseId, fromSem })
    e.dataTransfer.effectAllowed = "move"
  }

  const handleDragOver = (e: React.DragEvent, semIndex: number) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = "move"
    setDragOverSem(semIndex)
  }

  const handleDrop = (e: React.DragEvent, toSem: number) => {
    e.preventDefault()
    if (!dragInfo || dragInfo.fromSem === toSem) {
      setDragInfo(null)
      setDragOverSem(null)
      return
    }
    const { courseId, fromSem } = dragInfo
    const course = semesters[fromSem].find((c) => c.id === courseId)
    if (!course) return
    const updated = semesters.map((sem, i) => {
      if (i === fromSem) return sem.filter((c) => c.id !== courseId)
      if (i === toSem) return [...sem, course]
      return sem
    })
    savePlan(updated)
    setDragInfo(null)
    setDragOverSem(null)
  }

  const totalCredits = semesters.flat().reduce((sum, c) => sum + c.credits, 0)
  const resetPlan = () => {
    const empty = getDefaultPlan()
    setSemesters(empty)
    localStorage.removeItem(STORAGE_KEY)
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h2 className="text-xl font-bold mb-1">Degree Planner</h2>
          <p className="text-sm text-muted-foreground">
            Drag and drop courses to build your semester plan. Saves automatically.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-sm text-muted-foreground">
            <span className="font-semibold text-foreground">{totalCredits.toFixed(1)}</span> credits planned
          </div>
          {saved && (
            <span className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
              <Save className="size-3" /> Saved
            </span>
          )}
          <Button variant="ghost" size="sm" onClick={resetPlan} className="gap-1.5 text-muted-foreground hover:text-red-500">
            <RotateCcw className="size-3.5" />
            Reset
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {semesters.map((sem, semIndex) => {
          const semCredits = sem.reduce((sum, c) => sum + c.credits, 0)
          const isOver = dragOverSem === semIndex
          return (
            <div
              key={semIndex}
              className={`rounded-xl border-2 transition-colors ${
                isOver
                  ? "border-primary bg-primary/5"
                  : "border-border bg-card/50"
              }`}
              onDragOver={(e) => handleDragOver(e, semIndex)}
              onDragLeave={() => setDragOverSem(null)}
              onDrop={(e) => handleDrop(e, semIndex)}
            >
              <div className="flex items-center justify-between px-4 py-3 border-b border-border/60">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    {SEMESTER_LABELS[semIndex]}
                  </p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {sem.length} courses · {semCredits.toFixed(1)} cr
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="size-7 text-muted-foreground hover:text-foreground"
                  onClick={() => setAddTarget(addTarget === semIndex ? null : semIndex)}
                >
                  <Plus className="size-4" />
                </Button>
              </div>

              <div className="p-3 space-y-2 min-h-[80px]">
                {sem.map((course) => (
                  <div
                    key={course.id}
                    draggable
                    onDragStart={(e) => handleDragStart(e, course.id, semIndex)}
                    className="flex items-center justify-between gap-2 px-3 py-2 bg-background rounded-lg border border-border cursor-grab active:cursor-grabbing hover:border-primary/40 transition-colors group"
                  >
                    <div className="min-w-0">
                      <span className="font-mono text-sm font-semibold text-foreground">{course.code}</span>
                      {course.name && (
                        <span className="ml-2 text-xs text-muted-foreground truncate">{course.name}</span>
                      )}
                    </div>
                    <button
                      onClick={() => removeCourse(semIndex, course.id)}
                      className="text-muted-foreground hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100"
                    >
                      <X className="size-3.5" />
                    </button>
                  </div>
                ))}

                {sem.length === 0 && !isOver && (
                  <p className="text-xs text-muted-foreground text-center py-4">Drop courses here</p>
                )}

                {addTarget === semIndex && (
                  <div className="flex gap-2 mt-2">
                    <input
                      autoFocus
                      type="text"
                      value={addInput}
                      onChange={(e) => setAddInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") addCourse(semIndex)
                        if (e.key === "Escape") { setAddTarget(null); setAddInput("") }
                      }}
                      placeholder="SYSC 3110"
                      className="flex-1 px-2.5 py-1.5 text-sm rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary/30 font-mono"
                    />
                    <Button size="sm" onClick={() => addCourse(semIndex)} className="px-3">
                      Add
                    </Button>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      <div className="rounded-xl border border-border bg-secondary/20 p-4">
        <div className="flex items-center gap-2 mb-2 text-sm font-semibold">
          <GraduationCap className="size-4 text-primary" />
          Tips
        </div>
        <ul className="text-xs text-muted-foreground space-y-1">
          <li>• Drag courses between semesters to rearrange your plan</li>
          <li>• Click + to add a course — type the code (e.g. SYSC 3110) and press Enter</li>
          <li>• Your plan saves automatically to your browser</li>
          <li>• Most Carleton courses are 0.5 credit units — you typically need 20 total to graduate</li>
        </ul>
      </div>
    </div>
  )
}
