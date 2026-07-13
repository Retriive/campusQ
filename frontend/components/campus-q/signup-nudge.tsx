"use client"

import { SignUpButton } from "@clerk/nextjs"
import { track } from "@vercel/analytics"
import { X } from "lucide-react"

interface SignupNudgeProps {
  onDismiss: () => void
}

export function SignupNudge({ onDismiss }: SignupNudgeProps) {
  return (
    <div className="mx-4 mb-2 md:mx-0 flex items-center gap-2.5 rounded-xl border border-border/50 bg-secondary/50 px-3 py-2.5 animate-in fade-in slide-in-from-bottom-1 duration-200">
      <p className="flex-1 min-w-0 text-xs text-muted-foreground leading-snug">
        Enjoying the answer? Create a free account — it helps us keep CampusQ growing.
      </p>
      <SignUpButton mode="redirect">
        <button
          type="button"
          onClick={() => {
            try { track("signup_nudge_click", { surface: "chat_after_answer" }) } catch {}
          }}
          className="shrink-0 text-xs font-semibold px-3 py-1.5 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors active:scale-[0.98]"
        >
          Sign up free
        </button>
      </SignUpButton>
      <button
        type="button"
        onClick={onDismiss}
        aria-label="Dismiss sign up reminder"
        className="shrink-0 size-8 flex items-center justify-center rounded-lg text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
      >
        <X className="size-3.5" />
      </button>
    </div>
  )
}
