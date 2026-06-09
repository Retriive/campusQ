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
  Calculator,
  CalendarDays,
  Info,
  Clock,
  Trash2,
  PenLine,
  Pencil,
  Check,
  X,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useCampus } from "./campus-context"

export type View = "chat" | "programs" | "compare" | "gpa" | "deadlines"

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
  onRenameSession: (id: string, title: string) => void
  onOpenFeedback: () => void
}

const NAV_ITEMS: { view: View; icon: React.ElementType; label: string }[] = [
  { view: "chat",      icon: MessageSquare, label: "Chat"           },
  { view: "programs",  icon: BookOpen,      label: "Programs"       },
  { view: "compare",   icon: BarChart2,     label: "Compare"        },
  { view: "gpa",       icon: Calculator,    label: "GPA Calculator" },
  { view: "deadlines", icon: CalendarDays,  label: "Deadlines"      },
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
  onRenameSession,
  onOpenFeedback,
}: SidebarProps) {
  const { theme } = useCampus()
  const [hoverSession, setHoverSession] = React.useState<string | null>(null)
  const [renamingId, setRenamingId] = React.useState<string | null>(null)
  const [renameValue, setRenameValue] = React.useState("")

  const startRename = (id: string, title: string) => {
    setRenamingId(id)
    setRenameValue(title)
  }

  const commitRename = () => {
    if (renamingId && renameValue.trim()) onRenameSession(renamingId, renameValue.trim())
    setRenamingId(null)
  }

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
                    className={cn(
                      "group flex items-center gap-1 rounded-lg px-1 py-0.5 transition-colors",
                      currentSessionId === session.id ? "bg-secondary" : "hover:bg-secondary/50"
                    )}
                    onMouseEnter={() => setHoverSession(session.id)}
                    onMouseLeave={() => setHoverSession(null)}
                  >
                    {renamingId === session.id ? (
                      <>
                        <input
                          autoFocus
                          value={renameValue}
                          onChange={(e) => setRenameValue(e.target.value)}
                          onKeyDown={(e) => { if (e.key === "Enter") commitRename(); if (e.key === "Escape") setRenamingId(null) }}
                          className="flex-1 bg-background border border-border rounded px-2 py-0.5 text-xs outline-none"
                        />
                        <button onClick={commitRename} className="p-1 text-primary rounded shrink-0">
                          <Check className="size-3" />
                        </button>
                        <button onClick={() => setRenamingId(null)} className="p-1 text-muted-foreground rounded shrink-0">
                          <X className="size-3" />
                        </button>
                      </>
                    ) : (
                      <>
                        <button
                          onClick={() => onSelectSession(session.id)}
                          className={cn(
                            "flex-1 text-left px-1.5 py-1 text-xs transition-colors truncate",
                            currentSessionId === session.id
                              ? "text-foreground"
                              : "text-muted-foreground hover:text-foreground"
                          )}
                        >
                          {session.title}
                        </button>
                        {hoverSession === session.id && (
                          <>
                            <button
                              onClick={(e) => { e.stopPropagation(); startRename(session.id, session.title) }}
                              className="p-1 text-muted-foreground/50 hover:text-foreground transition-colors rounded shrink-0"
                            >
                              <Pencil className="size-3" />
                            </button>
                            <button
                              onClick={(e) => { e.stopPropagation(); onDeleteSession(session.id) }}
                              className="p-1 text-muted-foreground/50 hover:text-red-400 transition-colors rounded shrink-0"
                            >
                              <Trash2 className="size-3" />
                            </button>
                          </>
                        )}
                      </>
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
