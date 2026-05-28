"use client"

import { Plus, FileText, Layers, Paperclip } from "lucide-react"
import { useRef } from "react"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"

interface KnowledgeFile {
  id: string
  name: string
  status: "indexed" | "processing" | "error"
}

interface SidebarProps {
  files: KnowledgeFile[]
  onNewChat: () => void
  onAttachFile: (file: File) => void // Prop to pass the file to the chat
}

export function Sidebar({ files, onNewChat, onAttachFile }: SidebarProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    onAttachFile(file)
    if (fileInputRef.current) {
      fileInputRef.current.value = "" // Reset input
    }
  }

  return (
    <aside className="fixed left-0 top-0 z-30 hidden h-screen w-[280px] flex-col border-r border-sidebar-border bg-sidebar md:flex">
      {/* Header */}
      <div className="flex h-16 items-center gap-3 px-5">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-accent shadow-md shadow-primary/20">
          <Layers className="h-5 w-5 text-primary-foreground" />
        </div>
        <div className="flex flex-col">
          <span className="text-sm font-bold tracking-tight text-sidebar-foreground">
            OCDSB
          </span>
          <span className="text-xs font-medium text-primary/80">
            Knowledge Base
          </span>
        </div>
      </div>

      {/* Buttons */}
      <div className="flex gap-2 px-4 pb-4">
        <Button
          onClick={onNewChat}
          className="flex-1 justify-center gap-2 rounded-xl bg-gradient-to-r from-primary to-primary/80 font-semibold text-primary-foreground shadow-lg shadow-primary/25 transition-all hover:shadow-xl hover:shadow-primary/30"
        >
          <Plus className="h-4 w-4" />
          New Chat
        </Button>
        <Button
          variant="outline"
          size="icon"
          onClick={() => fileInputRef.current?.click()}
          title="Attach file to message"
          className="rounded-xl border-primary/20 text-primary hover:bg-primary/10 transition-all"
        >
          <Paperclip className="h-4 w-4" />
        </Button>
        <input
          type="file"
          accept=".pdf"
          className="hidden"
          ref={fileInputRef}
          onChange={handleFileSelect}
        />
      </div>

      <div className="mx-4 h-px bg-gradient-to-r from-transparent via-sidebar-border to-transparent" />

      {/* Knowledge Base List (Permanent Files) */}
      <div className="flex-1 overflow-hidden px-4 pt-4">
        <div className="mb-3 flex items-center gap-2">
          <span className="text-[11px] font-bold uppercase tracking-widest text-muted-foreground">
            Indexed Documents
          </span>
          <span className="rounded-full bg-gradient-to-r from-primary to-accent px-2.5 py-0.5 text-[10px] font-bold text-primary-foreground shadow-sm">
            {files.length}
          </span>
        </div>
        <ScrollArea className="h-[calc(100vh-220px)]">
          <div className="space-y-1.5 pr-2">
            {files.map((file) => (
              <div
                key={file.id}
                className="group flex items-center gap-3 rounded-xl border border-transparent px-3 py-3 transition-all hover:border-primary/20 hover:bg-sidebar-accent"
              >
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-amber-500/20 to-orange-500/20 shadow-sm">
                  <FileText className="h-4 w-4 text-amber-600" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[13px] font-semibold text-sidebar-foreground">
                    {file.name}
                  </p>
                  <div className="flex items-center gap-1.5">
                    {file.status === "indexed" && (
                      <>
                        <span className="h-2 w-2 rounded-full bg-gradient-to-r from-emerald-400 to-green-500 shadow-sm shadow-emerald-400/50" />
                        <span className="text-[11px] font-medium text-emerald-600">Ready</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>

      {/* Footer */}
      <div className="border-t border-sidebar-border p-4">
        <div className="flex items-center justify-between text-[11px]">
          <span className="font-medium text-muted-foreground">Powered by RAG</span>
          <span className="flex items-center gap-1.5 font-semibold text-emerald-600">
            <span className="h-2 w-2 rounded-full bg-gradient-to-r from-emerald-400 to-green-500 shadow-sm shadow-emerald-400/50" />
            Online
          </span>
        </div>
      </div>
    </aside>
  )
}