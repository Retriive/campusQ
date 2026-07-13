"use client"

import { SignUpButton } from "@clerk/nextjs"
import { track } from "@vercel/analytics"

interface GuestLimitWallProps {
  limit: number
}

export function GuestLimitWall({ limit }: GuestLimitWallProps) {
  return (
    <div className="mx-4 mb-3 md:mx-0 rounded-xl border border-border/60 bg-secondary/40 px-4 py-4 text-center animate-in fade-in slide-in-from-bottom-1 duration-200">
      <p className="text-sm font-semibold text-foreground">
        You’ve used today’s {limit} free questions
      </p>
      <p className="mt-1 text-xs text-muted-foreground leading-snug">
        Sign up free to keep asking — and unlock chat history across devices. Resets tomorrow.
      </p>
      <SignUpButton mode="redirect">
        <button
          type="button"
          onClick={() => {
            try { track("guest_limit_signup_click") } catch {}
          }}
          className="mt-3 inline-flex items-center justify-center rounded-lg bg-primary px-4 py-2 text-xs font-semibold text-primary-foreground hover:bg-primary/90 transition-colors active:scale-[0.98]"
        >
          Sign up free
        </button>
      </SignUpButton>
    </div>
  )
}
