"use client"

import { Sparkles } from "lucide-react"
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
            "max-w-[85%] md:max-w-[70%] rounded-2xl px-4 py-3 shadow-sm",
            theme.bgClass,
            "text-white"
          )}
        >
          <p className="text-[15px] leading-relaxed">{content}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex gap-3">
      <div className={cn(
        "shrink-0 size-8 rounded-lg flex items-center justify-center",
        theme.bgClass
      )}>
        <Sparkles className="size-4 text-white" />
      </div>
      <div className="flex-1 space-y-3 pt-1">
        
        {/* 🚀 The ReactMarkdown renderer */}
        <div className="text-[15px] text-foreground leading-relaxed">
          <ReactMarkdown
            components={{
              h3: ({node, ...props}) => <h3 className="text-lg font-bold mt-4 mb-2 text-foreground" {...props} />,
              p: ({node, ...props}) => <p className="mb-3 last:mb-0" {...props} />,
              strong: ({node, ...props}) => <strong className="font-semibold text-foreground" {...props} />,
              hr: ({node, ...props}) => <hr className="my-4 border-border/50" {...props} />,
            }}
          >
            {content}
          </ReactMarkdown>
        </div>

        {/* This renders your Course Cards below the text! */}
        {children}
        
      </div>
    </div>
  )
}