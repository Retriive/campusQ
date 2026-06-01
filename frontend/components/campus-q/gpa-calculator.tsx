"use client"

import * as React from "react"
import { Plus, Trash2, TrendingUp, GraduationCap, Info } from "lucide-react"
import { cn } from "@/lib/utils"
import { useCampus } from "./campus-context"

// Carleton University 12-point grading scale
const GRADE_SCALE = [
  { label: "A+", points: 12 },
  { label: "A",  points: 11 },
  { label: "A-", points: 10 },
  { label: "B+", points: 9  },
  { label: "B",  points: 8  },
  { label: "B-", points: 7  },
  { label: "C+", points: 6  },
  { label: "C",  points: 5  },
  { label: "C-", points: 4  },
  { label: "D+", points: 3  },
  { label: "D",  points: 2  },
  { label: "D-", points: 1  },
  { label: "F",  points: 0  },
] as const

const CREDIT_OPTIONS = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0]

const STANDING_LABELS = [
  { min: 11, label: "High Distinction", color: "text-emerald-500" },
  { min: 9,  label: "Distinction",      color: "text-blue-500"    },
  { min: 7,  label: "Good Standing",    color: "text-foreground"  },
  { min: 4,  label: "Passing",          color: "text-amber-500"   },
  { min: 0,  label: "Below Average",    color: "text-red-400"     },
]

interface CourseRow {
  id: string
  code: string
  credits: number
  grade: string
}

function makeRow(): CourseRow {
  return { id: Math.random().toString(36).slice(2), code: "", credits: 0.5, grade: "B" }
}

function calcGPA(rows: CourseRow[]): number | null {
  const valid = rows.filter((r) => r.grade !== "")
  if (!valid.length) return null
  const totalCredits = valid.reduce((s, r) => s + r.credits, 0)
  if (totalCredits === 0) return null
  const totalPoints = valid.reduce((s, r) => {
    const g = GRADE_SCALE.find((g) => g.label === r.grade)
    return s + (g?.points ?? 0) * r.credits
  }, 0)
  return totalPoints / totalCredits
}

function getStanding(gpa: number) {
  return STANDING_LABELS.find((s) => gpa >= s.min) ?? STANDING_LABELS[STANDING_LABELS.length - 1]
}

function GpaDisplay({ value, label, sub }: { value: number | null; label: string; sub?: string }) {
  const { theme } = useCampus()
  return (
    <div className="flex-1 flex flex-col items-center gap-1 py-5 rounded-2xl border border-border bg-card">
      <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground/50">{label}</p>
      {value !== null ? (
        <>
          <p className={cn("text-4xl font-bold tabular-nums tracking-tight", theme.textClass)}>
            {value.toFixed(2)}
          </p>
          <p className={cn("text-xs font-medium", getStanding(value).color)}>
            {getStanding(value).label}
          </p>
        </>
      ) : (
        <p className="text-4xl font-bold text-muted-foreground/20">—</p>
      )}
      {sub && <p className="text-[10px] text-muted-foreground/40 mt-0.5">{sub}</p>}
    </div>
  )
}

function CourseTable({
  rows,
  onChange,
  onAdd,
  onRemove,
  label,
  accent,
}: {
  rows: CourseRow[]
  onChange: (id: string, field: keyof CourseRow, value: string | number) => void
  onAdd: () => void
  onRemove: (id: string) => void
  label: string
  accent?: boolean
}) {
  const { theme } = useCampus()

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-foreground">{label}</h3>
        <button
          onClick={onAdd}
          className={cn(
            "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors",
            accent
              ? `${theme.bgClass} text-white hover:opacity-90`
              : "border border-border text-muted-foreground hover:text-foreground hover:bg-secondary"
          )}
        >
          <Plus className="size-3" />
          Add Course
        </button>
      </div>

      {rows.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border py-6 text-center">
          <p className="text-xs text-muted-foreground/50">No courses added yet</p>
        </div>
      ) : (
        <div className="rounded-xl border border-border overflow-hidden">
          <div className="grid grid-cols-[1fr_80px_80px_36px] gap-0 bg-secondary/30 border-b border-border">
            {["Course (optional)", "Credits", "Grade", ""].map((h) => (
              <div key={h} className="px-3 py-2 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/50">
                {h}
              </div>
            ))}
          </div>

          {rows.map((row, i) => (
            <div
              key={row.id}
              className={cn(
                "grid grid-cols-[1fr_80px_80px_36px] gap-0 items-center",
                i < rows.length - 1 && "border-b border-border/40"
              )}
            >
              <input
                value={row.code}
                onChange={(e) => onChange(row.id, "code", e.target.value)}
                placeholder="e.g. COMP 1005"
                className="px-3 py-2.5 text-xs bg-transparent focus:outline-none text-foreground placeholder:text-muted-foreground/30 font-mono"
              />
              <select
                value={row.credits}
                onChange={(e) => onChange(row.id, "credits", parseFloat(e.target.value))}
                className="px-2 py-2.5 text-xs bg-transparent focus:outline-none text-foreground border-l border-border/40 cursor-pointer"
              >
                {CREDIT_OPTIONS.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
              <select
                value={row.grade}
                onChange={(e) => onChange(row.id, "grade", e.target.value)}
                className="px-2 py-2.5 text-xs bg-transparent focus:outline-none text-foreground border-l border-border/40 cursor-pointer"
              >
                {GRADE_SCALE.map((g) => (
                  <option key={g.label} value={g.label}>{g.label} ({g.points})</option>
                ))}
              </select>
              <button
                onClick={() => onRemove(row.id)}
                className="flex items-center justify-center h-full text-muted-foreground/30 hover:text-red-400 transition-colors border-l border-border/40"
              >
                <Trash2 className="size-3" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export function GpaCalculator() {
  const { theme } = useCampus()
  const [completed, setCompleted] = React.useState<CourseRow[]>([makeRow(), makeRow()])
  const [planned, setPlanned] = React.useState<CourseRow[]>([])

  const updateRow = (rows: CourseRow[], setRows: React.Dispatch<React.SetStateAction<CourseRow[]>>) =>
    (id: string, field: keyof CourseRow, value: string | number) => {
      setRows(rows.map((r) => r.id === id ? { ...r, [field]: value } : r))
    }

  const removeRow = (rows: CourseRow[], setRows: React.Dispatch<React.SetStateAction<CourseRow[]>>) =>
    (id: string) => setRows(rows.filter((r) => r.id !== id))

  const currentGpa = calcGPA(completed)
  const projectedGpa = calcGPA([...completed, ...planned])

  const totalCredits = completed.reduce((s, r) => s + r.credits, 0)
  const plannedCredits = planned.reduce((s, r) => s + r.credits, 0)

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div>
        <h2 className="text-lg font-semibold mb-0.5">GPA Calculator</h2>
        <p className="text-sm text-muted-foreground">
          Carleton's 12-point scale — calculate your current CGPA and project future scenarios.
        </p>
      </div>

      {/* GPA displays */}
      <div className="flex gap-3">
        <GpaDisplay
          value={currentGpa}
          label="Current CGPA"
          sub={totalCredits > 0 ? `${totalCredits.toFixed(2)} credits` : undefined}
        />
        {planned.length > 0 && (
          <GpaDisplay
            value={projectedGpa}
            label="Projected CGPA"
            sub={plannedCredits > 0 ? `+${plannedCredits.toFixed(2)} credits planned` : undefined}
          />
        )}
      </div>

      {/* Grade scale reference */}
      <div className="rounded-xl border border-border bg-card p-4">
        <div className="flex items-center gap-2 mb-3">
          <Info className="size-3.5 text-muted-foreground/50" />
          <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground/50">Carleton Grade Scale</p>
        </div>
        <div className="grid grid-cols-4 sm:grid-cols-7 gap-1.5">
          {GRADE_SCALE.map((g) => (
            <div key={g.label} className="flex flex-col items-center gap-0.5 px-2 py-1.5 rounded-lg bg-secondary/40">
              <span className="text-xs font-semibold text-foreground">{g.label}</span>
              <span className="text-[10px] text-muted-foreground/60">{g.points}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Completed courses */}
      <CourseTable
        rows={completed}
        onChange={updateRow(completed, setCompleted)}
        onAdd={() => setCompleted([...completed, makeRow()])}
        onRemove={removeRow(completed, setCompleted)}
        label="Completed Courses"
        accent
      />

      {/* Planned courses (what-if) */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <TrendingUp className="size-4 text-muted-foreground/50" />
          <h3 className="text-sm font-semibold text-foreground">What-If: Planned Courses</h3>
        </div>
        <p className="text-xs text-muted-foreground">
          Add courses you plan to take to see how they'll affect your CGPA.
        </p>
        <CourseTable
          rows={planned}
          onChange={updateRow(planned, setPlanned)}
          onAdd={() => setPlanned([...planned, makeRow()])}
          onRemove={removeRow(planned, setPlanned)}
          label=""
        />
      </div>

      {/* Target CGPA helper */}
      <TargetHelper currentGpa={currentGpa} completedCredits={totalCredits} />
    </div>
  )
}

function TargetHelper({ currentGpa, completedCredits }: { currentGpa: number | null; completedCredits: number }) {
  const { theme } = useCampus()
  const [target, setTarget] = React.useState("10")
  const [futureCredits, setFutureCredits] = React.useState("2.5")

  const targetNum = parseFloat(target)
  const futureNum = parseFloat(futureCredits)

  let needed: number | null = null
  if (
    currentGpa !== null &&
    completedCredits > 0 &&
    !isNaN(targetNum) &&
    !isNaN(futureNum) &&
    futureNum > 0 &&
    targetNum >= 0 &&
    targetNum <= 12
  ) {
    needed = ((targetNum * (completedCredits + futureNum)) - (currentGpa * completedCredits)) / futureNum
  }

  const neededGrade = needed !== null ? GRADE_SCALE.slice().reverse().find((g) => g.points <= Math.ceil(needed!)) : null

  return (
    <div className="rounded-xl border border-border bg-card p-4 space-y-3">
      <div className="flex items-center gap-2">
        <GraduationCap className="size-4 text-muted-foreground/50" />
        <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground/50">Target CGPA</p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-xs text-muted-foreground mb-1 block">Target CGPA (0–12)</label>
          <input
            type="number"
            min={0}
            max={12}
            step={0.5}
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-border bg-secondary/30 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
          />
        </div>
        <div>
          <label className="text-xs text-muted-foreground mb-1 block">Credits remaining</label>
          <input
            type="number"
            min={0.5}
            step={0.5}
            value={futureCredits}
            onChange={(e) => setFutureCredits(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-border bg-secondary/30 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
          />
        </div>
      </div>

      {needed !== null && (
        <div className={cn("rounded-lg px-4 py-3 text-sm", needed > 12 ? "bg-red-500/10 text-red-400" : "bg-secondary")}>
          {needed > 12 ? (
            <p>Not achievable — the required average ({needed.toFixed(2)}) exceeds the maximum of 12.</p>
          ) : needed < 0 ? (
            <p className="text-emerald-500">You've already exceeded this target! 🎉</p>
          ) : (
            <p>
              You need an average of{" "}
              <span className={cn("font-bold", theme.textClass)}>{needed.toFixed(2)}</span>
              {neededGrade && (
                <> — roughly <span className="font-semibold">{neededGrade.label}</span></>
              )}{" "}
              across your remaining {futureNum} credits.
            </p>
          )}
        </div>
      )}
    </div>
  )
}
