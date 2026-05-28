"use client"

import { FileText, ChevronDown } from "lucide-react"
import { useState } from "react"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"

export interface Source {
  id: string
  fileName: string
  sectionTitle: string
  snippet: string
}

export interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  sources?: Source[]
}

interface ChatMessageProps {
  message: Message
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user"

  return (
    <div className={`flex w-full ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-[85%] ${isUser ? "ml-12" : "mr-12"}`}>
        {/* Message Content */}
        <div
          className={`${
            isUser
              ? "rounded-2xl bg-gradient-to-r from-primary to-primary/90 px-5 py-3.5 text-primary-foreground shadow-lg shadow-primary/20"
              : "text-foreground"
          }`}
        >
          <p className="whitespace-pre-wrap text-[15px] leading-relaxed">
            {message.content}
          </p>
        </div>

        {/* Sources Section (AI messages only) */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <SourcesCitation sources={message.sources} />
        )}
      </div>
    </div>
  )
}

function SourcesCitation({ sources }: { sources: Source[] }) {
  const [openSources, setOpenSources] = useState<Set<string>>(new Set())

  const toggleSource = (id: string) => {
    setOpenSources((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  return (
    <div className="mt-5">
      <p className="mb-3 text-[11px] font-bold uppercase tracking-widest text-muted-foreground">
        Sources
      </p>
      <div className="space-y-2">
        {sources.map((source, index) => {
          const colors = [
            { gradient: "from-amber-500/20 to-orange-500/20", icon: "text-amber-600", border: "border-amber-500/30" },
            { gradient: "from-rose-500/20 to-pink-500/20", icon: "text-rose-500", border: "border-rose-500/30" },
            { gradient: "from-emerald-500/20 to-teal-500/20", icon: "text-emerald-600", border: "border-emerald-500/30" },
          ]
          const color = colors[index % colors.length]
          
          return (
            <Collapsible
              key={source.id}
              open={openSources.has(source.id)}
              onOpenChange={() => toggleSource(source.id)}
            >
              <CollapsibleTrigger asChild>
                <button className={`group flex w-full items-center gap-3 rounded-xl border bg-card px-4 py-3 text-left shadow-sm transition-all hover:shadow-md ${openSources.has(source.id) ? color.border : 'border-border'}`}>
                  <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br ${color.gradient} shadow-sm`}>
                    <FileText className={`h-4 w-4 ${color.icon}`} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-semibold text-foreground">
                      {source.fileName}
                    </p>
                    <p className="truncate text-xs text-muted-foreground">
                      {source.sectionTitle}
                    </p>
                  </div>
                  <ChevronDown
                    className={`h-4 w-4 shrink-0 text-muted-foreground transition-transform duration-200 ${
                      openSources.has(source.id) ? "rotate-180" : ""
                    }`}
                  />
                </button>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <div className={`mt-2 rounded-xl border-l-4 ${color.border} bg-muted/50 px-4 py-3`}>
                  <p className="font-mono text-[13px] leading-relaxed text-muted-foreground">
                    {source.snippet}
                  </p>
                </div>
              </CollapsibleContent>
            </Collapsible>
          )
        })}
      </div>
    </div>
  )
}
