"use client"

import { useCampus } from "./campus-context"
import { cn } from "@/lib/utils"
import ReactMarkdown from "react-markdown"

interface ChatMessageProps {
  role: "user" | "assistant"
  content: string
  children?: React.ReactNode
}

export function ChatMessage({ role, content, children }: ChatMessageProps) {
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
      {/* Avatar */}
      <div className={cn(
        "shrink-0 size-6 rounded-md flex items-center justify-center mt-0.5 text-[10px] font-bold text-white",
        theme.bgClass
      )}>
        Q
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 space-y-3 pt-0.5">
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
        {children}
      </div>
    </div>
  )
}
