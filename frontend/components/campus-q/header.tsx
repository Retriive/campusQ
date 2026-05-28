"use client"

import { Moon, Sun } from "lucide-react"
import { Button } from "@/components/ui/button"
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
    <header className="sticky top-0 z-50 w-full border-b border-border/50 bg-background/90 backdrop-blur-xl">
      <div className="flex items-center justify-between px-4 md:px-6 h-12">

        {/* Wordmark */}
        <span className="text-sm font-semibold tracking-tight text-foreground select-none">
          Campus<span className={cn(theme.textClass)}>Q</span>
        </span>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggleDark}
            className="size-8 text-muted-foreground hover:text-foreground"
          >
            {isDark ? <Sun className="size-3.5" /> : <Moon className="size-3.5" />}
          </Button>

          {isLoaded && (
            isSignedIn ? (
              <UserButton
                afterSignOutUrl="/"
                appearance={{
                  elements: { avatarBox: "size-7" },
                }}
              />
            ) : (
              <SignInButton mode="modal">
                <button className="text-xs font-medium border border-border px-3 py-1.5 rounded-lg text-foreground hover:bg-secondary transition-colors">
                  Sign in
                </button>
              </SignInButton>
            )
          )}
        </div>

      </div>
    </header>
  )
}
