"use client"

import { Moon, Sun, History } from "lucide-react"
import { SignUpButton, UserButton, useUser } from "@clerk/nextjs"
import { useCampus } from "./campus-context"
import { cn } from "@/lib/utils"

interface HeaderProps {
  isDark: boolean
  onToggleDark: () => void
  onOpenHistory?: () => void
  onHome?: () => void
}

export function Header({ isDark, onToggleDark, onOpenHistory, onHome }: HeaderProps) {
  const { theme } = useCampus()
  const { isSignedIn, isLoaded } = useUser()

  return (
    <header className="h-12 shrink-0 flex items-center justify-between px-4 border-b border-border/40 bg-card">
      {/* Wordmark — tap to return home. Shown on every breakpoint. */}
      <div className="flex items-center gap-1.5">
        <button
          type="button"
          onClick={onHome}
          aria-label="Back to home"
          className="text-sm font-semibold tracking-tight text-foreground select-none cursor-pointer transition-opacity duration-150 ease-[var(--ease-out)] hover:opacity-70 active:scale-[0.98]"
        >
          Campus<span className={theme.textClass}>Q</span>
        </button>
        <span className="text-[10px] font-medium px-1.5 py-0.5 rounded-full bg-secondary text-muted-foreground select-none">
          beta
        </span>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-0.5 md:gap-1">
        {onOpenHistory && (
          <button
            onClick={onOpenHistory}
            className="md:hidden size-10 flex items-center justify-center rounded-lg text-muted-foreground hover:text-foreground hover:bg-secondary active:bg-secondary transition-colors"
            aria-label="Chat history"
          >
            <History className="size-[18px]" />
          </button>
        )}
        <button
          onClick={onToggleDark}
          aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
          className="size-10 md:size-8 flex items-center justify-center rounded-lg text-muted-foreground hover:text-foreground hover:bg-secondary active:bg-secondary transition-colors"
        >
          {isDark ? <Sun className="size-[18px] md:size-3.5" /> : <Moon className="size-[18px] md:size-3.5" />}
        </button>

        {isLoaded && (
          isSignedIn ? (
            <UserButton afterSignOutUrl="/" appearance={{ elements: { avatarBox: "size-7" } }} />
          ) : (
            <SignUpButton mode="redirect">
              <button className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors active:scale-[0.98]">
                Save chats
              </button>
            </SignUpButton>
          )
        )}
      </div>
    </header>
  )
}
