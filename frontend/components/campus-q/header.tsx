"use client"

import { Moon, Sun } from "lucide-react"
import { SignInButton, UserButton, useUser } from "@clerk/nextjs"
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
    <header className="h-14 shrink-0 flex items-center justify-between px-4 md:px-6 border-b border-border/40 bg-card">

      {/* Left — empty, wordmark is in sidebar */}
      <div />

      {/* Right — actions */}
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
            <SignInButton mode="modal">
              <button className="text-xs font-medium px-3 py-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors">
                Sign in
              </button>
            </SignInButton>
          )
        )}
      </div>
    </header>
  )
}
