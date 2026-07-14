"use client"

import * as React from "react"
import { useCampus } from "./campus-context"
import { cn } from "@/lib/utils"
import ReactMarkdown from "react-markdown"
import { ExternalLink, ThumbsUp, ThumbsDown } from "lucide-react"

interface Source {
  url: string
  title: string
  section?: string
}

/**
 * Returns the url only if it's a safe http(s) link, otherwise undefined.
 * Model output and citation metadata are untrusted, so javascript:/data:
 * (and any other scheme) must never become a clickable anchor. Relative or
 * malformed values throw in the URL parser and are treated as unsafe.
 */
function safeHref(url: unknown): string | undefined {
  if (typeof url !== "string") return undefined
  try {
    const proto = new URL(url).protocol
    return proto === "http:" || proto === "https:" ? url : undefined
  } catch {
    return undefined
  }
}

interface ChatMessageProps {
  role: "user" | "assistant"
  content: string
  sources?: Source[]
  onFeedback?: (rating: "up" | "down") => void
  children?: React.ReactNode
}

function FeedbackButtons({ onFeedback }: { onFeedback: (rating: "up" | "down") => void }) {
  const [given, setGiven] = React.useState<"up" | "down" | null>(null)

  const handle = (rating: "up" | "down") => {
    if (given) return
    setGiven(rating)
    onFeedback(rating)
  }

  if (given) {
    return (
      <div className="flex items-center gap-1.5 mt-3 text-xs text-muted-foreground/60">
        {given === "up" ? <ThumbsUp className="size-3" /> : <ThumbsDown className="size-3" />}
        Thanks for the feedback
      </div>
    )
  }

  return (
    <div className="flex items-center gap-1 mt-3">
      <span className="text-[11px] text-muted-foreground/40 mr-1">Was this helpful?</span>
      <button
        onClick={() => handle("up")}
        aria-label="Helpful"
        className="p-1.5 rounded-md text-muted-foreground/40 hover:text-success hover:bg-success/10 transition-[color,background-color,transform] duration-150 ease-[var(--ease-out)] active:scale-90"
      >
        <ThumbsUp className="size-3.5" />
      </button>
      <button
        onClick={() => handle("down")}
        aria-label="Not helpful"
        className="p-1.5 rounded-md text-muted-foreground/40 hover:text-destructive hover:bg-destructive/10 transition-[color,background-color,transform] duration-150 ease-[var(--ease-out)] active:scale-90"
      >
        <ThumbsDown className="size-3.5" />
      </button>
    </div>
  )
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
    if (source.title && source.title.length > 3 && !/^[A-Z]{3,4}$/.test(source.title)) {
      return source.title.length > 56 ? source.title.slice(0, 56) + "…" : source.title
    }
    try {
      const parts = new URL(source.url).pathname.split("/").filter(Boolean)
      const slug = parts[parts.length - 1]?.replace(/-/g, " ") || "Source"
      return slug.length > 56 ? slug.slice(0, 56) + "…" : slug
    } catch {
      return "Source"
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
          href={safeHref(s.url)}
          target="_blank"
          rel="noopener noreferrer"
          title={s.section ? `${formatTitle(s)} — ${s.section}` : formatTitle(s)}
          style={{ animationDelay: `${i * 45}ms` }}
          className="stagger-item group inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-border bg-card hover:bg-secondary hover:border-border/80 transition-[background-color,border-color,color,transform] duration-150 ease-[var(--ease-out)] active:scale-[0.98] text-xs text-muted-foreground hover:text-foreground max-w-[240px]"
        >
          <span className="size-1.5 rounded-full bg-success shrink-0" aria-hidden />
          <span className="flex flex-col min-w-0">
            <span className="truncate capitalize">{formatTitle(s)}</span>
            {s.section && (
              <span className="truncate text-[10px] text-muted-foreground/60 normal-case">
                {s.section}
              </span>
            )}
          </span>
          <ExternalLink className="size-2.5 shrink-0 opacity-40 group-hover:opacity-70 transition-opacity" />
        </a>
      ))}
    </div>
  )
}

function ChatMessageInner({ role, content, sources, onFeedback, children }: ChatMessageProps) {
  const { theme } = useCampus()

  if (role === "user") {
    return (
      <div className="flex justify-end animate-message-in">
        <div className="max-w-[75%] md:max-w-[60%] rounded-2xl rounded-br-md px-4 py-3 bg-secondary border border-border text-foreground shadow-resting">
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{content}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex gap-3 animate-message-in">
      <div className={cn(
        "shrink-0 size-6 rounded-md flex items-center justify-center mt-0.5 text-[10px] font-bold text-primary-foreground shadow-resting ring-1 ring-black/5",
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
                a: ({ node, href, ...props }) => {
                  const safe = safeHref(href)
                  if (!safe) return <span {...props} />
                  return (
                    <a className={cn("underline underline-offset-2 hover:opacity-70 transition-opacity", theme.textClass)}
                      href={safe} target="_blank" rel="noopener noreferrer" {...props} />
                  )
                },
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

        {onFeedback && content !== "" && (
          <FeedbackButtons onFeedback={onFeedback} />
        )}
      </div>
    </div>
  )
}

/** Memoized so completed messages don't re-render on every streaming token. */
export const ChatMessage = React.memo(ChatMessageInner)
