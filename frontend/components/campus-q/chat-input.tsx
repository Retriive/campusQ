"use client"

import * as React from "react"
import { ArrowUp } from "lucide-react"
import { useCampus } from "./campus-context"
import { cn } from "@/lib/utils"

// Phone-width inputs clip past ~18–20 chars at 16px.
const PLACEHOLDER_STRINGS = [
  "SYSC 3110 prereqs?",
  "CS degree courses?",
  "Credits to graduate?",
  "What is COMP 2804?",
  "Take COMP 3000 yet?",
  "Year 3 electives?",
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
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }, [value])

  const canSubmit = value.trim().length > 0 && !disabled

  return (
    <div className={cn(
      isHome
        ? "px-0 pb-0 pt-0"
        : "px-3 pt-2 pb-2 md:px-4 md:pt-3 md:pb-4 sticky bottom-0 z-10 bg-gradient-to-t from-background via-background/95 to-transparent"
    )}>
      <div className="max-w-2xl mx-auto">

        {/* Input box — fuller capsule on mobile */}
        <div className={cn(
          "relative flex items-end border bg-card transition-[box-shadow,border-color] duration-200 ease-[var(--ease-out)]",
          "rounded-[22px] md:rounded-2xl",
          "focus-within:border-primary/55 focus-within:ring-[3px] focus-within:ring-primary/12",
          isHome
            ? "shadow-raised border-border/80"
            : "shadow-resting border-border/70",
          value && "border-border"
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
            className={cn(
              "flex-1 resize-none bg-transparent outline-none text-foreground",
              "placeholder:text-muted-foreground/45",
              "text-[16px] md:text-sm leading-relaxed",
              "min-h-[52px] md:min-h-[52px] max-h-[140px]",
              "py-3.5 pl-4 pr-[52px] md:py-[14px] md:pl-4 md:pr-14"
            )}
          />

          <button
            type="button"
            onClick={() => onSubmit()}
            disabled={!canSubmit}
            aria-label="Send message"
            className={cn(
              "absolute right-2 bottom-2 size-10 md:size-8 rounded-full md:rounded-xl",
              "flex items-center justify-center",
              "transition-[transform,opacity,background-color] duration-150 ease-[var(--ease-out)]",
              canSubmit
                ? cn(theme.bgClass, theme.hoverBgClass, "text-primary-foreground shadow-resting active:scale-90")
                : "bg-secondary text-muted-foreground/30 cursor-not-allowed"
            )}
          >
            <ArrowUp className="size-4 md:size-3.5" strokeWidth={2.5} />
          </button>
        </div>

        <p className="text-[11px] text-center text-muted-foreground/60 mt-2.5 leading-relaxed">
          CampusQ is AI and can make mistakes — check important decisions with your advisor.
        </p>
      </div>
    </div>
  )
}
