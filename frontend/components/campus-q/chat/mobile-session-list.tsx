"use client"

import * as React from "react"
import { Check, Pencil, Trash2, X } from "lucide-react"
import { cn } from "@/lib/utils"
import type { ChatSession } from "../sidebar"

interface MobileSessionListProps {
  sessions: ChatSession[]
  currentSessionId: string
  onSelect: (id: string) => void
  onDelete: (id: string) => void
  onRename: (id: string, title: string) => void
}

export function MobileSessionList({
  sessions,
  currentSessionId,
  onSelect,
  onDelete,
  onRename,
}: MobileSessionListProps) {
  const [renamingId, setRenamingId] = React.useState<string | null>(null)
  const [renameValue, setRenameValue] = React.useState("")

  const startRename = (id: string, currentTitle: string) => {
    setRenamingId(id)
    setRenameValue(currentTitle)
  }

  const commitRename = () => {
    if (renamingId) onRename(renamingId, renameValue)
    setRenamingId(null)
  }

  return (
    <div className="flex-1 overflow-y-auto px-3 pb-4">
      {sessions.length === 0 ? (
        <p className="text-xs text-muted-foreground text-center pt-6">
          No past chats yet
        </p>
      ) : (
        <div className="space-y-0.5">
          {sessions.map((session) => (
            <div
              key={session.id}
              className={cn(
                "flex items-center gap-1 rounded-lg px-1 py-1 transition-colors",
                currentSessionId === session.id
                  ? "bg-secondary"
                  : "hover:bg-secondary/50",
              )}
            >
              {renamingId === session.id ? (
                <>
                  <input
                    autoFocus
                    value={renameValue}
                    onChange={(event) => setRenameValue(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter") commitRename()
                      if (event.key === "Escape") setRenamingId(null)
                    }}
                    className="flex-1 bg-background border border-border rounded px-2 py-1 text-xs outline-none"
                  />
                  <button onClick={commitRename} className="p-1 text-primary rounded">
                    <Check className="size-3.5" />
                  </button>
                  <button
                    onClick={() => setRenamingId(null)}
                    className="p-1 text-muted-foreground rounded"
                  >
                    <X className="size-3.5" />
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={() => onSelect(session.id)}
                    className="flex-1 text-left px-2 py-2.5 text-[13px] truncate text-muted-foreground data-[active=true]:text-foreground"
                    data-active={currentSessionId === session.id}
                  >
                    {session.title}
                  </button>
                  <button
                    onClick={() => startRename(session.id, session.title)}
                    aria-label="Rename chat"
                    className="size-9 flex items-center justify-center text-muted-foreground/50 hover:text-foreground active:bg-secondary transition-colors rounded-lg shrink-0"
                  >
                    <Pencil className="size-3.5" />
                  </button>
                  <button
                    onClick={() => onDelete(session.id)}
                    aria-label="Delete chat"
                    className="size-9 flex items-center justify-center text-muted-foreground/50 hover:text-destructive active:bg-destructive/10 transition-colors rounded-lg shrink-0"
                  >
                    <Trash2 className="size-3.5" />
                  </button>
                </>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
