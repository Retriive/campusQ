"use client"

import { useCampus } from "./campus-context"
import { cn } from "@/lib/utils"
import ReactMarkdown from "react-markdown"
import { ExternalLink } from "lucide-react"

interface Source {
  url: string
  title: string
}

interface ChatMessageProps {
  role: "user" | "assistant"
  content: string
  sources?: Source[]
  children?: React.ReactNode
}

function TypingCursor() {
  return (
    <div className="flex items-center gap-1 py-1">
      <span className="size-1.5 rounded-full bg-muted-foreground/30 animate-[pulse_1.2s_ease-in-out_infinite]" />
      <span className="size-1.5 rounded-full bg-muted-foreground/30 animate-[pulse_1.2s_ease-in-out_0.4s_infinite]" />
      <span className="size-1.5 rounded-full bg-muted-foreground/30 animate-[pulse_1.2s_ease-in-out_0.8s_infinite]" />
    </div>
  )
}

function Sources({ sources }: { sources: Source[] }) {
  if (!sources.length) return null

  const formatTitle = (source: Source): string => {
    if (source.title && source.title.length > 3) {
      return source.title.length > 48 ? source.title.slice(0, 48) + "…" : source.title
    }
    try {
      const parts = new URL(source.url).pathname.split("/").filter(Boolean)
      return (parts[parts.length - 1]?.replace(/-/g, " ") || "Source")
    } catch {
      return "Source"
    }
  }

  const formatDomain = (url: string): string => {
    try {
      return new URL(url).hostname.replace("www.", "")
    } catch {
      return ""
    }
  }

  return (
    <div className="mt-3 flex items-center gap-2 flex-wrap">
      <span className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/40 shrink-0">
        Sources
      </span>
      {sources.map((s, i) => (
        <a
          key={i}
          href={s.url}
          target="_blank"
          rel="noopener noreferrer"
          className="group inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-border bg-secondary/50 hover:bg-secondary hover:border-border/80 transition-all text-xs text-muted-foreground hover:text-foreground"
        >
          <span className="truncate max-w-[160px] capitalize">{formatTitle(s)}</span>
          <ExternalLink className="size-2.5 shrink-0 opacity-40 group-hover:opacity-70 transition-opacity" />
        </a>
      ))}
    </div>
  )
}

export function ChatMessage({ role, content, sources, children }: ChatMessageProps) {
  const { theme } = useCampus()

  if (role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[75%] md:max-w-[60%] rounded-2xl rounded-br-sm px-4 py-3 bg-foreground text-background">
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{content}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex gap-3">
      <div className={cn(
        "shrink-0 size-6 rounded-md flex items-center justify-center mt-0.5 text-[10px] font-bold text-white",
        theme.bgClass
      )}>
        Q
      </div>

      <div className="flex-1 min-w-0 space-y-3 pt-0.5">
        {content === "" ? (
          <TypingCursor />
        ) : (
          <div className="prose-campusq text-sm leading-relaxed text-foreground">
            <ReactMarkdown
              components={{
                p: ({ node, ...props }) => (
                  <p className="mb-3 last:mb-0 leading-[1.7]" {...props} />
                ),
                h1: ({ node, ...props }) => (
                  <h1 className="text-base font-semibold mt-5 mb-2 text-foreground" {...props} />
                ),
                h2: ({ node, ...props }) => (
                  <h2 className="text-sm font-semibold mt-4 mb-2 text-foreground" {...props} />
                ),
                h3: ({ node, ...props }) => (
                  <h3 className="text-sm font-semibold mt-3 mb-1.5 text-foreground" {...props} />
                ),
                strong: ({ node, ...props }) => (
                  <strong className="font-semibold text-foreground" {...props} />
                ),
                ul: ({ node, ...props }) => (
                  <ul className="mb-3 space-y-1.5 pl-4" {...props} />
                ),
                ol: ({ node, ...props }) => (
                  <ol className="mb-3 space-y-1.5 pl-4 list-decimal" {...props} />
                ),
                li: ({ node, ...props }) => (
                  <li className="leading-relaxed text-foreground/90 list-disc marker:text-muted-foreground" {...props} />
                ),
                code: ({ node, ...props }) => (
                  <code className="px-1.5 py-0.5 rounded-md bg-secondary text-xs font-mono text-foreground" {...props} />
                ),
                hr: ({ node, ...props }) => (
                  <hr className="my-4 border-border/50" {...props} />
                ),
                a: ({ node, ...props }) => (
                  <a className={cn("underline underline-offset-2 hover:opacity-70 transition-opacity", theme.textClass)}
                    target="_blank" rel="noopener noreferrer" {...props} />
                ),
                blockquote: ({ node, ...props }) => (
                  <blockquote className="border-l-2 border-border pl-3 text-muted-foreground italic" {...props} />
                ),
              }}
            >
              {content}
            </ReactMarkdown>
          </div>
        )}

        {children}

        {sources && sources.length > 0 && content !== "" && (
          <Sources sources={sources} />
        )}
      </div>
    </div>
  )
}
