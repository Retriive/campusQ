"use client"

import * as React from "react"
import Link from "next/link"
import {
  MessageSquarePlus,
  ChevronLeft,
  ChevronRight,
  Database,
  AlertCircle,
  ShieldCheck,
  MessageSquare,
  GraduationCap,
  BookOpen,
  BarChart2,
  Sparkles,
  Info,
  Clock,
  Trash2,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { useCampus } from "./campus-context"

export type View = "chat" | "planner" | "programs" | "compare" | "eligible"

export interface ChatSession {
  id: string
  title: string
  createdAt: number
}

interface SidebarProps {
  onNewChat: () => void
  collapsed: boolean
  onToggle: () => void
  currentView: View
  onViewChange: (view: View) => void
  sessions: ChatSession[]
  currentSessionId: string
  onSelectSession: (id: string) => void
  onDeleteSession: (id: string) => void
  onOpenFeedback: () => void
}

const NAV_ITEMS: { view: View; icon: React.ElementType; label: string }[] = [
  { view: "chat", icon: MessageSquare, label: "Chat" },
  { view: "planner", icon: GraduationCap, label: "Degree Planner" },
  { view: "programs", icon: BookOpen, label: "Programs" },
  { view: "compare", icon: BarChart2, label: "Compare" },
  { view: "eligible", icon: Sparkles, label: "What Can I Take?" },
]

export function Sidebar({
  onNewChat,
  collapsed,
  onToggle,
  currentView,
  onViewChange,
  sessions,
  currentSessionId,
  onSelectSession,
  onDeleteSession,
  onOpenFeedback,
}: SidebarProps) {
  const { theme } = useCampus()
  const [docCount, setDocCount] = React.useState<string>("—")
  const [hoverSession, setHoverSession] = React.useState<string | null>(null)

  React.useEffect(() => {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
    fetch(`${API_URL}/api/documents`)
      .then((r) => r.json())
      .then((d) => { if (d.count != null) setDocCount(Number(d.count).toLocaleString()) })
      .catch(() => setDocCount("—"))
  }, [])

  return (
    <aside
      className={cn(
        "h-full border-r border-border/50 bg-card/50 backdrop-blur-sm flex flex-col transition-all duration-300 ease-in-out shrink-0",
        collapsed ? "w-16" : "w-64"
      )}
    >
      {/* Header */}
      <div className={cn("p-4 flex items-center", collapsed ? "justify-center" : "justify-between")}>
        {!collapsed && (
          <div className="flex items-center gap-2">
            <div className={cn("size-6 rounded-lg flex items-center justify-center", theme.bgClass)}>
              <Sparkles className="size-3.5 text-white" />
            </div>
            <span className="text-sm font-bold">CampusQ</span>
          </div>
        )}
        <Button variant="ghost" size="icon" className="size-8 text-muted-foreground hover:text-foreground" onClick={onToggle}>
          {collapsed ? <ChevronRight className="size-4" /> : <ChevronLeft className="size-4" />}
        </Button>
      </div>

      {/* New Chat */}
      <div className="px-3 mb-2">
        <Button
          onClick={onNewChat}
          className={cn("w-full gap-2 bg-primary hover:bg-primary/90 text-primary-foreground", collapsed && "px-0")}
        >
          <MessageSquarePlus className="size-4" />
          {!collapsed && <span>New Chat</span>}
        </Button>
      </div>

      {/* Navigation */}
      <div className="px-2 mb-3">
        {!collapsed && (
          <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground px-2 mb-1">Tools</p>
        )}
        <nav className="space-y-0.5">
          {NAV_ITEMS.map(({ view, icon: Icon, label }) => (
            <button
              key={view}
              onClick={() => onViewChange(view)}
              className={cn(
                "w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
                currentView === view
                  ? "bg-primary/10 text-primary font-medium"
                  : "text-muted-foreground hover:text-foreground hover:bg-secondary/60",
                collapsed && "justify-center px-0"
              )}
              title={collapsed ? label : undefined}
            >
              <Icon className="size-4 shrink-0" />
              {!collapsed && <span>{label}</span>}
            </button>
          ))}
        </nav>
      </div>

      {/* Chat History */}
      {!collapsed && sessions.length > 0 && (
        <div className="px-2 flex-1 overflow-y-auto min-h-0">
          <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground px-2 mb-1">Recent Chats</p>
          <div className="space-y-0.5">
            {sessions.slice(0, 15).map((session) => (
              <div
                key={session.id}
                className="relative group"
                onMouseEnter={() => setHoverSession(session.id)}
                onMouseLeave={() => setHoverSession(null)}
              >
                <button
                  onClick={() => onSelectSession(session.id)}
                  className={cn(
                    "w-full text-left px-3 py-2 rounded-lg text-xs transition-colors pr-8",
                    currentSessionId === session.id
                      ? "bg-primary/10 text-primary"
                      : "text-muted-foreground hover:text-foreground hover:bg-secondary/60"
                  )}
                >
                  <div className="flex items-center gap-1.5 mb-0.5">
                    <Clock className="size-3 shrink-0 opacity-60" />
                    <span className="truncate font-medium">{session.title}</span>
                  </div>
                </button>
                {hoverSession === session.id && (
                  <button
                    onClick={(e) => { e.stopPropagation(); onDeleteSession(session.id) }}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-red-500 transition-colors"
                  >
                    <Trash2 className="size-3" />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Collapsed: spacer */}
      {collapsed && <div className="flex-1" />}

      {/* Stats + Bottom */}
      <div className="p-3 border-t border-border/50 space-y-2">
        {!collapsed && (
          <div className="bg-secondary/50 rounded-xl p-3 mb-2">
            <div className="flex items-center gap-2 mb-1">
              <Database className="size-3.5 text-primary" />
              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Indexed</span>
            </div>
            <div className="text-2xl font-bold text-foreground">{docCount}</div>
            <div className="text-xs text-muted-foreground">documents</div>
          </div>
        )}

        <Button
          variant="ghost"
          size="sm"
          onClick={onOpenFeedback}
          className={cn(
            "w-full gap-2 text-muted-foreground hover:text-foreground text-xs",
            collapsed && "px-0"
          )}
        >
          <AlertCircle className="size-3.5" />
          {!collapsed && <span>Report a Problem</span>}
        </Button>

        {!collapsed && (
          <Link
            href="/about"
            className="flex items-center gap-2 px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors rounded-lg hover:bg-secondary/60"
          >
            <Info className="size-3.5" />
            About CampusQ
          </Link>
        )}

        <div className={cn("flex items-center gap-2 px-3 py-1", collapsed && "justify-center px-0")}>
          <span className="relative flex size-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
            <span className="relative inline-flex rounded-full size-2 bg-green-500" />
          </span>
          {!collapsed && <span className="text-xs text-muted-foreground">Online</span>}
        </div>
      </div>
    </aside>
  )
}
