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
        <div
          className={cn(
            "max-w-[80%] md:max-w-[65%] rounded-2xl rounded-br-md px-4 py-3",
            theme.bgClass,
            "text-white"
          )}
        >
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{content}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex gap-3 group">
      {/* Avatar */}
      <div className={cn(
        "shrink-0 size-7 rounded-lg flex items-center justify-center mt-0.5 font-bold text-xs text-white",
        theme.bgClass
      )}>
        Q
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 space-y-3">
        <div className={cn(
          "text-sm leading-relaxed text-foreground",
          "[&>*:first-child]:mt-0 [&>*:last-child]:mb-0"
        )}>
          <ReactMarkdown
            components={{
              p: ({ node, ...props }) => (
                <p className="mb-3 last:mb-0 leading-relaxed" {...props} />
              ),
              h1: ({ node, ...props }) => (
                <h1 className="text-base font-bold mt-5 mb-2" {...props} />
              ),
              h2: ({ node, ...props }) => (
                <h2 className="text-base font-bold mt-4 mb-2" {...props} />
              ),
              h3: ({ node, ...props }) => (
                <h3 className="text-sm font-semibold mt-4 mb-1.5 text-foreground" {...props} />
              ),
              strong: ({ node, ...props }) => (
                <strong className="font-semibold text-foreground" {...props} />
              ),
              ul: ({ node, ...props }) => (
                <ul className="mb-3 space-y-1 pl-4" {...props} />
              ),
              ol: ({ node, ...props }) => (
                <ol className="mb-3 space-y-1 pl-4 list-decimal" {...props} />
              ),
              li: ({ node, ...props }) => (
                <li className="leading-relaxed text-foreground/90 list-disc" {...props} />
              ),
              code: ({ node, ...props }) => (
                <code className="px-1.5 py-0.5 rounded bg-secondary text-xs font-mono" {...props} />
              ),
              hr: ({ node, ...props }) => (
                <hr className="my-4 border-border/40" {...props} />
              ),
              a: ({ node, ...props }) => (
                <a className="text-primary underline underline-offset-2 hover:opacity-80" target="_blank" rel="noopener noreferrer" {...props} />
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
