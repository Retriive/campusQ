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
} from "reactflow"
import "reactflow/dist/style.css"
import dagre from "@dagrejs/dagre"
import { Loader2, RotateCcw } from "lucide-react"
import { cn } from "@/lib/utils"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

// ── Types ─────────────────────────────────────────────────────────────────────
interface CourseNode { code: string; name: string; credits: number }
interface CourseEdge  { source: string; target: string }

type NodeStatus = "completed" | "available" | "locked"

// ── Dagre auto-layout ─────────────────────────────────────────────────────────
const NODE_W = 160
const NODE_H = 64

function applyDagreLayout(nodes: Node[], edges: Edge[]): Node[] {
  const g = new dagre.graphlib.Graph()
  g.setDefaultEdgeLabel(() => ({}))
  g.setGraph({ rankdir: "TB", ranksep: 60, nodesep: 24 })
  nodes.forEach((n) => g.setNode(n.id, { width: NODE_W, height: NODE_H }))
  edges.forEach((e) => g.setEdge(e.source, e.target))
  dagre.layout(g)
  return nodes.map((n) => {
    const { x, y } = g.node(n.id)
    return { ...n, position: { x: x - NODE_W / 2, y: y - NODE_H / 2 } }
  })
}

// ── Course node component ─────────────────────────────────────────────────────
function CourseNodeCard({ data }: NodeProps) {
  const { code, name, status, credits, onToggle } = data as {
    code: string; name: string; status: NodeStatus; credits: number; onToggle: () => void
  }

  const bg =
    status === "completed" ? "bg-emerald-500 border-emerald-600 text-white" :
    status === "available"  ? "bg-primary/10 border-primary text-foreground" :
                              "bg-card border-border text-muted-foreground"

  return (
    <div
      onClick={onToggle}
      className={cn(
        "rounded-xl border-2 px-3 py-2 cursor-pointer select-none transition-all hover:-translate-y-0.5 hover:shadow-md",
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

const nodeTypes = { course: CourseNodeCard }

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

// ── Main component ─────────────────────────────────────────────────────────────
export function DegreePlan({
  slug,
  variant,
}: {
  slug: string
  variant: string
}) {
  const [courses, setCourses]     = React.useState<CourseNode[]>([])
  const [rawEdges, setRawEdges]   = React.useState<CourseEdge[]>([])
  const [loading, setLoading]     = React.useState(false)
  const [error, setError]         = React.useState("")
  const [completed, setCompleted] = React.useState<Set<string>>(new Set())

  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])

  // Load plan from backend
  React.useEffect(() => {
    if (!slug || !variant) return
    setLoading(true)
    setError("")
    fetch(`${API_URL}/api/degree-plan?slug=${encodeURIComponent(slug)}&variant=${encodeURIComponent(variant)}`)
      .then((r) => r.json())
      .then((d) => {
        setCourses(d.courses || [])
        setRawEdges(d.edges || [])
        setCompleted(loadCompleted(slug, variant))
      })
      .catch(() => setError("Failed to load plan. Make sure the backend is running."))
      .finally(() => setLoading(false))
  }, [slug, variant])

  // Rebuild graph whenever courses, edges, or completed changes
  React.useEffect(() => {
    if (!courses.length) return
    const statuses = computeStatuses(courses, rawEdges, completed)

    const rfEdges: Edge[] = rawEdges.map((e) => ({
      id: `${e.source}-${e.target}`,
      source: e.source,
      target: e.target,
      style: { stroke: "hsl(var(--border))", strokeWidth: 1.5 },
      animated: false,
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
        onToggle: () => toggleCourse(c.code),
      },
    }))

    const laid = applyDagreLayout(rfNodes, rfEdges)
    setNodes(laid)
    setEdges(rfEdges)
  }, [courses, rawEdges, completed])

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
      Select a program and variant to see your plan.
    </div>
  )

  return (
    <div className="flex flex-col gap-3 h-full">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <span className="size-2.5 rounded-full bg-emerald-500 inline-block" /> Completed
          </div>
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <span className="size-2.5 rounded-full bg-primary/40 inline-block" /> Can take now
          </div>
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <span className="size-2.5 rounded-full bg-border inline-block" /> Locked
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-muted-foreground">{doneCount}/{totalCount} done</span>
          {doneCount > 0 && (
            <button
              onClick={resetPlan}
              className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              <RotateCcw className="size-3" /> Reset
            </button>
          )}
        </div>
      </div>

      {/* Progress bar */}
      <div className="h-1.5 rounded-full bg-secondary overflow-hidden">
        <div
          className="h-full bg-emerald-500 transition-all duration-500 rounded-full"
          style={{ width: totalCount ? `${(doneCount / totalCount) * 100}%` : "0%" }}
        />
      </div>

      {/* Graph */}
      <div className="flex-1 rounded-xl border border-border overflow-hidden" style={{ minHeight: 480 }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          nodesDraggable={false}
          nodesConnectable={false}
          elementsSelectable={false}
          proOptions={{ hideAttribution: true }}
        >
          <Background color="hsl(var(--border))" gap={20} size={1} />
          <Controls showInteractive={false} />
        </ReactFlow>
      </div>

      <p className="text-[10px] text-muted-foreground/50 text-center">
        Click any course to mark it complete. Progress is saved automatically.
      </p>
    </div>
  )
}
