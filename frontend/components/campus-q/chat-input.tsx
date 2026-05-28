"use client"

import * as React from "react"
import { Paperclip, ArrowUp } from "lucide-react"
import { Button } from "@/components/ui/button"
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
      if (value.trim()) {
        onSubmit()
      }
    }
  }

  React.useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`
    }
  }, [value])

  return (
    <div className="sticky bottom-0 bg-gradient-to-t from-background via-background to-transparent pt-6 pb-4 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="relative flex items-end gap-2 rounded-2xl border border-border/60 bg-card p-2.5 shadow-lg shadow-black/5">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="shrink-0 size-9 rounded-xl text-muted-foreground hover:text-foreground hover:bg-secondary"
            disabled
            title="PDF upload coming soon"
          >
            <Paperclip className="size-4" />
          </Button>
          
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about courses, professors, departments..."
            className="flex-1 resize-none bg-transparent border-0 outline-none text-[15px] text-foreground placeholder:text-muted-foreground/60 min-h-[40px] max-h-[160px] py-2 px-1 leading-normal"
            rows={1}
            disabled={disabled}
          />
          
          <Button
            type="button"
            size="icon"
            onClick={onSubmit}
            disabled={!value.trim() || disabled}
            className={cn(
              "shrink-0 size-9 rounded-xl transition-all duration-200",
              value.trim() 
                ? cn(theme.bgClass, "text-white shadow-md hover:opacity-90 hover:shadow-lg") 
                : "bg-secondary text-muted-foreground"
            )}
          >
            <ArrowUp className="size-4" />
          </Button>
        </div>
        <p className="text-[11px] text-center text-muted-foreground/50 mt-3">
          CampusQ may produce inaccurate information. Verify important details.
        </p>
      </div>
    </div>
  )
}
