"use client"

import { useState, useRef, useEffect } from "react"
import { Paperclip, ArrowUp } from "lucide-react"
import { Button } from "@/components/ui/button"

interface ChatInputProps {
  onSend: (message: string) => void
  disabled?: boolean
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [input, setInput] = useState("")
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSubmit = () => {
    if (input.trim() && !disabled) {
      onSend(input.trim())
      setInput("")
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = "auto"
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`
    }
  }, [input])

  return (
    <div className="fixed bottom-0 left-0 right-0 md:left-[280px]">
      {/* Gradient Fade */}
      <div className="pointer-events-none h-24 bg-gradient-to-t from-background via-background/80 to-transparent" />
      
      {/* Input Container */}
      <div className="bg-background px-4 pb-6">
        <div className="mx-auto max-w-3xl">
          <div className="relative flex items-end gap-2 rounded-2xl border border-border bg-card shadow-2xl shadow-primary/10">
            {/* Upload Button */}
            <button
              type="button"
              className="mb-3 ml-3 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-muted-foreground transition-all hover:bg-gradient-to-br hover:from-amber-500/10 hover:to-orange-500/10 hover:text-amber-600"
              aria-label="Upload context"
            >
              <Paperclip className="h-5 w-5" />
            </button>

            {/* Text Input */}
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about OCDSB policies..."
              disabled={disabled}
              rows={1}
              className="max-h-[200px] min-h-[52px] flex-1 resize-none bg-transparent py-4 text-[15px] text-foreground outline-none placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-50"
            />

            {/* Send Button */}
            <Button
              onClick={handleSubmit}
              disabled={!input.trim() || disabled}
              size="icon"
              className="mb-3 mr-3 h-10 w-10 shrink-0 rounded-xl bg-gradient-to-r from-primary to-primary/90 text-primary-foreground shadow-lg shadow-primary/25 transition-all hover:shadow-xl hover:shadow-primary/30 disabled:bg-muted disabled:text-muted-foreground disabled:shadow-none"
            >
              <ArrowUp className="h-5 w-5" />
            </Button>
          </div>

          {/* Disclaimer */}
          <p className="mt-4 text-center text-xs font-medium text-muted-foreground">
            AI can make mistakes. Always verify with official OCDSB policies.
          </p>
        </div>
      </div>
    </div>
  )
}
