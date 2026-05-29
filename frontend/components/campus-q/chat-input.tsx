"use client"

import * as React from "react"
import { ArrowUp } from "lucide-react"
import { useCampus } from "./campus-context"
import { cn } from "@/lib/utils"

interface ChatInputProps {
  value: string
  onChange: (value: string) => void
  onSubmit: () => void
  disabled?: boolean
}

export function ChatInput({ value, onChange, onSubmit, disabled }: ChatInputProps) {
  const { theme } = useCampus()
  const textareaRef = React.useRef<HTMLTextAreaElement>(null)

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      if (value.trim() && !disabled) onSubmit()
    }
  }

  React.useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = "auto"
    el.style.height = `${Math.min(el.scrollHeight, 180)}px`
  }, [value])

  const canSubmit = value.trim().length > 0 && !disabled

  return (
    <div className="sticky bottom-0 z-10 px-4 pb-5 pt-4 bg-gradient-to-t from-background via-background/95 to-transparent">
      <div className="max-w-3xl mx-auto">
        <div className={cn(
          "relative flex items-end rounded-2xl border bg-card shadow-sm transition-shadow duration-200",
          value ? "border-border shadow-md" : "border-border/60",
          disabled && "opacity-60"
        )}>
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about courses, prerequisites, programs…"
            rows={1}
            disabled={disabled}
            className="flex-1 resize-none bg-transparent outline-none text-sm text-foreground placeholder:text-muted-foreground/50 min-h-[52px] max-h-[180px] py-4 pl-4 pr-12 leading-relaxed"
          />

          <button
            type="button"
            onClick={onSubmit}
            disabled={!canSubmit}
            className={cn(
              "absolute right-2.5 bottom-2.5 size-8 rounded-xl flex items-center justify-center transition-all duration-200",
              canSubmit
                ? cn(theme.bgClass, "text-white shadow-sm hover:opacity-90 hover:scale-105 active:scale-95")
                : "bg-secondary text-muted-foreground/40 cursor-not-allowed"
            )}
          >
            <ArrowUp className="size-4" strokeWidth={2.5} />
          </button>
        </div>

        <p className="text-[11px] text-center text-muted-foreground/40 mt-2.5">
          CampusQ may be inaccurate — verify important decisions with your advisor.
        </p>
      </div>
    </div>
  )
}
