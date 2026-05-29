"use client"

import * as React from "react"
import Link from "next/link"
import {
  MessageSquarePlus,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
  MessageSquare,
  BookOpen,
  BarChart2,
  Info,
  Clock,
  Trash2,
  PenLine,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useCampus } from "./campus-context"

export type View = "chat" | "programs" | "compare"

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
  { view: "programs", icon: BookOpen, label: "Programs" },
  { view: "compare", icon: BarChart2, label: "Compare" },
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
  const [hoverSession, setHoverSession] = React.useState<string | null>(null)

  return (
    <aside className={cn(
      "h-full border-r border-border/40 bg-card flex flex-col transition-all duration-300 ease-in-out shrink-0",
      collapsed ? "w-14" : "w-60"
    )}>

      {/* Top — logo + toggle */}
      <div className={cn(
        "h-14 flex items-center px-3 shrink-0",
        collapsed ? "justify-center" : "justify-between"
      )}>
        {!collapsed && (
          <span className="text-sm font-semibold tracking-tight text-foreground">
            Campus<span className={theme.textClass}>Q</span>
          </span>
        )}
        <button
          onClick={onToggle}
          className="size-8 flex items-center justify-center rounded-lg text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
        >
          {collapsed ? <ChevronRight className="size-4" /> : <ChevronLeft className="size-4" />}
        </button>
      </div>

      {/* New Chat */}
      <div className={cn("px-2 mb-4", collapsed && "px-1.5")}>
        <button
          onClick={onNewChat}
          className={cn(
            "w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors",
            "bg-foreground text-background hover:bg-foreground/90",
            collapsed && "justify-center px-0"
          )}
        >
          <PenLine className="size-3.5 shrink-0" />
          {!collapsed && <span>New Chat</span>}
        </button>
      </div>

      {/* Nav */}
      <nav className={cn("px-2 space-y-0.5 mb-4", collapsed && "px-1.5")}>
        {NAV_ITEMS.map(({ view, icon: Icon, label }) => (
          <button
            key={view}
            onClick={() => onViewChange(view)}
            title={collapsed ? label : undefined}
            className={cn(
              "w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors",
              currentView === view
                ? "bg-secondary text-foreground font-medium"
                : "text-muted-foreground hover:text-foreground hover:bg-secondary/60",
              collapsed && "justify-center px-0"
            )}
          >
            <Icon className="size-4 shrink-0" />
            {!collapsed && <span>{label}</span>}
          </button>
        ))}
      </nav>

      {/* Divider */}
      {!collapsed && <div className="mx-3 mb-3 border-t border-border/40" />}

      {/* Chat history */}
      {!collapsed && (
        <div className="flex-1 px-2 overflow-y-auto min-h-0">
          {sessions.length > 0 && (
            <>
              <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/50 px-2 mb-2">
                Recent
              </p>
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
                        "w-full text-left px-2.5 py-1.5 rounded-lg text-xs transition-colors pr-7",
                        currentSessionId === session.id
                          ? "bg-secondary text-foreground"
                          : "text-muted-foreground hover:text-foreground hover:bg-secondary/50"
                      )}
                    >
                      <span className="truncate block">{session.title}</span>
                    </button>
                    {hoverSession === session.id && (
                      <button
                        onClick={(e) => { e.stopPropagation(); onDeleteSession(session.id) }}
                        className="absolute right-1.5 top-1/2 -translate-y-1/2 p-1 text-muted-foreground/50 hover:text-red-400 transition-colors rounded"
                      >
                        <Trash2 className="size-3" />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {collapsed && <div className="flex-1" />}

      {/* Bottom */}
      <div className={cn("p-2 border-t border-border/40 space-y-0.5", collapsed && "p-1.5")}>
        <button
          onClick={onOpenFeedback}
          title={collapsed ? "Report a Problem" : undefined}
          className={cn(
            "w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs text-muted-foreground hover:text-foreground hover:bg-secondary/60 transition-colors",
            collapsed && "justify-center px-0"
          )}
        >
          <AlertCircle className="size-3.5 shrink-0" />
          {!collapsed && <span>Report a Problem</span>}
        </button>

        {!collapsed && (
          <Link
            href="/about"
            className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs text-muted-foreground hover:text-foreground hover:bg-secondary/60 transition-colors"
          >
            <Info className="size-3.5 shrink-0" />
            About
          </Link>
        )}
      </div>
    </aside>
  )
}
