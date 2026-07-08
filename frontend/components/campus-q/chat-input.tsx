"use client"

import * as React from "react"
import { ArrowUp } from "lucide-react"
import { useCampus } from "./campus-context"
import { cn } from "@/lib/utils"

const PLACEHOLDER_STRINGS = [
  "What are the prerequisites for SYSC 3110?",
  "What courses do I need for Software Engineering?",
  "How many credits to graduate from Computer Science?",
  "What is COMP 2804 about?",
  "Can I take SYSC 4906 without SYSC 4101?",
  "What electives can I take in third year?",
]

function useAnimatedPlaceholder(strings: string[], active: boolean) {
  const [displayed, setDisplayed] = React.useState("")
  const [index, setIndex] = React.useState(0)
  const [phase, setPhase] = React.useState<"typing" | "pausing" | "deleting">("typing")

  React.useEffect(() => {
    if (!active) return
    const current = strings[index]
    if (phase === "typing") {
      if (displayed.length < current.length) {
        const t = setTimeout(() => setDisplayed(current.slice(0, displayed.length + 1)), 38)
        return () => clearTimeout(t)
      } else {
        const t = setTimeout(() => setPhase("pausing"), 2400)
        return () => clearTimeout(t)
      }
    }
    if (phase === "pausing") {
      const t = setTimeout(() => setPhase("deleting"), 100)
      return () => clearTimeout(t)
    }
    if (phase === "deleting") {
      if (displayed.length > 0) {
        const t = setTimeout(() => setDisplayed(displayed.slice(0, -1)), 14)
        return () => clearTimeout(t)
      } else {
        setIndex((i) => (i + 1) % strings.length)
        setPhase("typing")
      }
    }
  }, [displayed, phase, index, strings, active])

  return displayed
}

interface ChatInputProps {
  value: string
  onChange: (value: string) => void
  onSubmit: () => void
  disabled?: boolean
  isHome?: boolean
}

export function ChatInput({ value, onChange, onSubmit, disabled, isHome }: ChatInputProps) {
  const { theme } = useCampus()
  const textareaRef = React.useRef<HTMLTextAreaElement>(null)
  const animatedPlaceholder = useAnimatedPlaceholder(PLACEHOLDER_STRINGS, !!isHome && !value)

  const placeholder = isHome
    ? (animatedPlaceholder || "Ask anything about Carleton…")
    : "Ask a follow-up…"

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
    <div className={cn(
      "px-4 pb-5",
      isHome
        ? "pt-0"
        : "pt-3 sticky bottom-0 z-10 bg-gradient-to-t from-background via-background/95 to-transparent"
    )}>
      <div className="max-w-2xl mx-auto">

        {/* Input box */}
        <div className={cn(
          "relative flex items-end rounded-2xl border bg-card transition-[box-shadow,border-color] duration-200 ease-[var(--ease-out)]",
          "focus-within:border-primary/60 focus-within:ring-[3px] focus-within:ring-primary/15",
          isHome
            ? "shadow-raised border-border/70 hover:shadow-overlay hover:border-border"
            : "shadow-resting border-border/60",
          value && !isHome && "border-border/80"
        )}>
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            rows={1}
            disabled={disabled}
            enterKeyHint="send"
            autoCapitalize="sentences"
            autoCorrect="on"
            spellCheck
            aria-label="Ask CampusQ a question"
            className="flex-1 resize-none bg-transparent outline-none text-base md:text-sm text-foreground placeholder:text-muted-foreground/40 min-h-[56px] md:min-h-[52px] max-h-[160px] py-[15px] md:py-[14px] pl-4 pr-14 leading-relaxed"
          />

          <button
            type="button"
            onClick={() => onSubmit()}
            disabled={!canSubmit}
            aria-label="Send message"
            className={cn(
              "absolute right-2 bottom-2 md:right-2.5 md:bottom-2.5 size-10 md:size-8 rounded-xl flex items-center justify-center transition-[transform,opacity,background-color] duration-150 ease-[var(--ease-out)]",
              canSubmit
                ? cn(theme.bgClass, theme.hoverBgClass, "text-primary-foreground shadow-resting active:scale-90")
                : "bg-secondary text-muted-foreground/25 cursor-not-allowed"
            )}
          >
            <ArrowUp className="size-4 md:size-3.5" strokeWidth={2.5} />
          </button>
        </div>

        {/* Disclaimer */}
        <p className="text-[11px] text-center text-muted-foreground/60 mt-2.5 tracking-wide">
          {isHome
            ? "Independent tool — not affiliated with Carleton University"
            : "CampusQ is AI and can make mistakes — verify important decisions with your advisor"          }
        </p>
      </div>
    </div>
  )
}
