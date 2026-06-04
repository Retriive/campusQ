"use client"

import { Moon, Sun } from "lucide-react"
import { SignUpButton, UserButton, useUser } from "@clerk/nextjs"
import { useCampus } from "./campus-context"
import { cn } from "@/lib/utils"

interface HeaderProps {
  isDark: boolean
  onToggleDark: () => void
}

export function Header({ isDark, onToggleDark }: HeaderProps) {
  const { theme } = useCampus()
  const { isSignedIn, isLoaded } = useUser()

  return (
    <header className="h-12 shrink-0 flex items-center justify-between px-4 border-b border-border/40 bg-card">
      {/* Wordmark — hidden on mobile (bottom nav handles nav) */}
      <div className="hidden md:flex items-center gap-1.5">
        <span className="text-sm font-semibold tracking-tight text-foreground select-none">
          Campus<span className={theme.textClass}>Q</span>
        </span>
        <span className="text-[10px] font-medium px-1.5 py-0.5 rounded-full bg-secondary text-muted-foreground select-none">
          beta
        </span>
      </div>

      {/* Mobile: just the wordmark centered */}
      <div className="md:hidden flex items-center gap-1.5">
        <span className="text-sm font-semibold tracking-tight text-foreground select-none">
          Campus<span className={theme.textClass}>Q</span>
        </span>
        <span className="text-[10px] font-medium px-1.5 py-0.5 rounded-full bg-secondary text-muted-foreground select-none">
          beta
        </span>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-1">
        <button
          onClick={onToggleDark}
          className="size-8 flex items-center justify-center rounded-lg text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
        >
          {isDark ? <Sun className="size-3.5" /> : <Moon className="size-3.5" />}
        </button>

        {isLoaded && (
          isSignedIn ? (
            <UserButton afterSignOutUrl="/" appearance={{ elements: { avatarBox: "size-7" } }} />
          ) : (
            <SignUpButton mode="redirect">
              <button className="text-xs font-medium px-3 py-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors">
                Sign up
              </button>
            </SignUpButton>
          )
        )}
      </div>
    </header>
  )
}
