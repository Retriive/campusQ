"use client"

import * as React from "react"
import ReactFlow, {
  Background,
  Controls,
  type Node,
  type Edge,
  type NodeProps,
  Handle,
  Position,
  useNodesState,
  useEdgesState,
  useReactFlow,
  ReactFlowProvider,
} from "reactflow"
import "reactflow/dist/style.css"
import { Loader2, RotateCcw } from "lucide-react"
import { cn } from "@/lib/utils"
import { API_BASE_URL } from "@/lib/api"

// ── Types ─────────────────────────────────────────────────────────────────────
interface CourseNode { code: string; name: string; credits: number }
interface CourseEdge  { source: string; target: string }

type NodeStatus = "completed" | "available" | "locked"

// ── Year-banded layout ────────────────────────────────────────────────────────
const NODE_W    = 160
const NODE_H    = 64
const COL_GAP   = 20
const ROW_GAP   = 56
const HEADER_H  = 32  // height of the year label row

function courseYear(code: string): number {
  const m = code.match(/\d{4}/)
  if (!m) return 5
  const lvl = parseInt(m[0][0])
  return lvl >= 1 && lvl <= 4 ? lvl : 5
}

function applyYearLayout(courseNodes: Node[]): Node[] {
  // Group by year
  const groups: Record<number, Node[]> = {}
  courseNodes.forEach((n) => {
    const yr = courseYear(n.id)
    ;(groups[yr] ||= []).push(n)
  })

  const yearKeys = Object.keys(groups).map(Number).sort()
  const result: Node[] = []

  yearKeys.forEach((yr, rowIdx) => {
    const rowY = rowIdx * (NODE_H + HEADER_H + ROW_GAP)
    const nodes = groups[yr]
    const totalW = nodes.length * NODE_W + (nodes.length - 1) * COL_GAP
    const startX = -totalW / 2

    nodes.forEach((n, colIdx) => {
      result.push({
        ...n,
        position: {
          x: startX + colIdx * (NODE_W + COL_GAP),
          y: rowY + HEADER_H,
        },
      })
    })
  })

  return result
}

// Year header node — non-interactive label
function YearHeaderNode({ data }: NodeProps) {
  return (
    <div className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/50 pointer-events-none select-none">
      {data.label}
    </div>
  )
}

// Build year header nodes to sit above each band
function buildYearHeaderNodes(courseNodes: Node[]): Node[] {
  const groups: Record<number, Node[]> = {}
  courseNodes.forEach((n) => {
    const yr = courseYear(n.id)
    ;(groups[yr] ||= []).push(n)
  })

  const yearKeys = Object.keys(groups).map(Number).sort()
  const YEAR_LABELS: Record<number, string> = { 1: "Year 1", 2: "Year 2", 3: "Year 3", 4: "Year 4", 5: "Other" }

  return yearKeys.map((yr, rowIdx) => {
    const rowY = rowIdx * (NODE_H + HEADER_H + ROW_GAP)
    const nodes = groups[yr]
    const totalW = nodes.length * NODE_W + (nodes.length - 1) * COL_GAP
    const startX = -totalW / 2
    return {
      id: `__year_${yr}`,
      type: "yearHeader",
      position: { x: startX, y: rowY },
      data: { label: YEAR_LABELS[yr] ?? `Year ${yr}` },
      selectable: false,
      draggable: false,
    }
  })
}

// ── Course node component ─────────────────────────────────────────────────────
function CourseNodeCard({ data }: NodeProps) {
  const { code, name, status, credits, onToggle } = data as {
    code: string; name: string; status: NodeStatus; credits: number; onToggle: () => void
  }

  const bg =
    status === "completed" ? "bg-success border-success text-white" :
    status === "available"  ? "bg-primary/10 border-primary text-foreground" :
                              "bg-card border-border text-muted-foreground"

  return (
    <div
      onClick={onToggle}
      className={cn(
        "rounded-xl border-2 px-3 py-2 cursor-pointer select-none transition-[transform,box-shadow,border-color] duration-200 ease-[var(--ease-out)] hover:-translate-y-0.5 hover:shadow-md active:scale-[0.98]",
        bg
      )}
      style={{ width: NODE_W, minHeight: NODE_H }}
    >
      <Handle type="target" position={Position.Top}    style={{ opacity: 0 }} />
      <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />
      <p className="text-[11px] font-bold font-mono leading-none mb-1">{code}</p>
      <p className="text-[10px] leading-tight line-clamp-2 opacity-80">{name}</p>
      <p className="text-[9px] mt-1 opacity-50">{credits} cr</p>
    </div>
  )
}

const nodeTypes = { course: CourseNodeCard, yearHeader: YearHeaderNode }

// ── localStorage helpers ──────────────────────────────────────────────────────
function storageKey(slug: string, variant: string) {
  return `campusq-plan-${slug}-${encodeURIComponent(variant)}`
}
function loadCompleted(slug: string, variant: string): Set<string> {
  try {
    const raw = localStorage.getItem(storageKey(slug, variant))
    return raw ? new Set(JSON.parse(raw)) : new Set()
  } catch { return new Set() }
}
function saveCompleted(slug: string, variant: string, completed: Set<string>) {
  try {
    localStorage.setItem(storageKey(slug, variant), JSON.stringify([...completed]))
  } catch {}
}

// ── Status computation ────────────────────────────────────────────────────────
function computeStatuses(
  courses: CourseNode[],
  edges: CourseEdge[],
  completed: Set<string>,
): Record<string, NodeStatus> {
  const prereqsOf: Record<string, string[]> = {}
  courses.forEach((c) => { prereqsOf[c.code] = [] })
  edges.forEach((e) => { prereqsOf[e.target]?.push(e.source) })

  const out: Record<string, NodeStatus> = {}
  courses.forEach((c) => {
    if (completed.has(c.code)) { out[c.code] = "completed"; return }
    const allMet = prereqsOf[c.code].every((p) => completed.has(p))
    out[c.code] = allMet ? "available" : "locked"
  })
  return out
}

// ── Inner graph (needs ReactFlowProvider context) ─────────────────────────────
function DegreePlanGraph({
  courses,
  rawEdges,
  completed,
  onToggle,
}: {
  courses: CourseNode[]
  rawEdges: CourseEdge[]
  completed: Set<string>
  onToggle: (code: string) => void
}) {
  const { fitView } = useReactFlow()
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])

  React.useEffect(() => {
    if (!courses.length) return

    const statuses = computeStatuses(courses, rawEdges, completed)

    const rfEdges: Edge[] = rawEdges.map((e) => ({
      id: `${e.source}->${e.target}`,
      source: e.source,
      target: e.target,
      style: { stroke: "oklch(70% 0 0)", strokeWidth: 1.5 },
    }))

    const rfNodes: Node[] = courses.map((c) => ({
      id: c.code,
      type: "course",
      position: { x: 0, y: 0 },
      data: {
        code: c.code,
        name: c.name,
        credits: c.credits,
        status: statuses[c.code],
        onToggle: () => onToggle(c.code),
      },
    }))

    const laid = applyYearLayout(rfNodes)
    const headers = buildYearHeaderNodes(rfNodes)
    setNodes([...headers, ...laid])
    setEdges(rfEdges)
    // fitView after layout is applied
    setTimeout(() => fitView({ padding: 0.15, duration: 200 }), 50)
  }, [courses, rawEdges, completed])

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      nodeTypes={nodeTypes}
      nodesDraggable={false}
      nodesConnectable={false}
      elementsSelectable={false}
      proOptions={{ hideAttribution: true }}
      minZoom={0.2}
    >
      <Background color="oklch(87% 0.004 85)" gap={20} size={1} />
      <Controls showInteractive={false} />
    </ReactFlow>
  )
}

// ── Main component ─────────────────────────────────────────────────────────────
export function DegreePlan({ slug, variant }: { slug: string; variant: string }) {
  const [courses, setCourses]     = React.useState<CourseNode[]>([])
  const [rawEdges, setRawEdges]   = React.useState<CourseEdge[]>([])
  const [loading, setLoading]     = React.useState(false)
  const [error, setError]         = React.useState("")
  const [completed, setCompleted] = React.useState<Set<string>>(new Set())

  React.useEffect(() => {
    if (!slug || !variant) return
    setLoading(true)
    setError("")
    setCourses([])
    setRawEdges([])
    fetch(`${API_BASE_URL}/api/degree-plan?slug=${encodeURIComponent(slug)}&variant=${encodeURIComponent(variant)}`)
      .then((r) => r.json())
      .then((d) => {
        setCourses(d.courses || [])
        setRawEdges(d.edges || [])
        setCompleted(loadCompleted(slug, variant))
      })
      .catch(() => setError("Failed to load plan. Make sure the backend is running."))
      .finally(() => setLoading(false))
  }, [slug, variant])

  const toggleCourse = React.useCallback((code: string) => {
    setCompleted((prev) => {
      const next = new Set(prev)
      next.has(code) ? next.delete(code) : next.add(code)
      saveCompleted(slug, variant, next)
      return next
    })
  }, [slug, variant])

  const resetPlan = () => {
    const empty = new Set<string>()
    saveCompleted(slug, variant, empty)
    setCompleted(empty)
  }

  const doneCount  = completed.size
  const totalCount = courses.length

  if (loading) return (
    <div className="flex items-center justify-center gap-2 text-muted-foreground py-20 text-sm">
      <Loader2 className="size-4 animate-spin" /> Building your plan…
    </div>
  )

  if (error) return (
    <div className="text-center py-12 text-sm text-muted-foreground">{error}</div>
  )

  if (!courses.length) return (
    <div className="text-center py-12 text-sm text-muted-foreground">
      No course data found for this program variant.
    </div>
  )

  return (
    <div className="flex flex-col gap-3">
      {/* Legend + count */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <span className="size-2.5 rounded-full bg-success inline-block" /> Completed
          </span>
          <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <span className="size-2.5 rounded-full bg-primary/30 border border-primary inline-block" /> Can take now
          </span>
          <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <span className="size-2.5 rounded-full bg-secondary border border-border inline-block" /> Locked
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-muted-foreground">{doneCount}/{totalCount} done</span>
          {doneCount > 0 && (
            <button onClick={resetPlan} className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors">
              <RotateCcw className="size-3" /> Reset
            </button>
          )}
        </div>
      </div>

      {/* Progress bar */}
      <div className="h-1.5 rounded-full bg-secondary overflow-hidden">
        <div
          className="h-full bg-success transition-[width] duration-500 ease-out rounded-full"
          style={{ width: totalCount ? `${(doneCount / totalCount) * 100}%` : "0%" }}
        />
      </div>

      {/* Graph — explicit pixel height so ReactFlow can measure */}
      <div className="rounded-xl border border-border overflow-hidden" style={{ height: 600 }}>
        <ReactFlowProvider>
          <DegreePlanGraph
            courses={courses}
            rawEdges={rawEdges}
            completed={completed}
            onToggle={toggleCourse}
          />
        </ReactFlowProvider>
      </div>

      <p className="text-[10px] text-muted-foreground/50 text-center">
        Click any course to mark it complete · progress saved automatically
      </p>
    </div>
  )
}
