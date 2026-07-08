"use client"

import { useEffect, useState } from "react"
import { Moon, Sun } from "lucide-react"

const STORAGE_KEY = "campusq-theme"

// Landing pages run their own light/dark track (see .landing-track in
// globals.css) independent of the app. Light is the default; the choice
// persists across marketing pages via localStorage.
export function useLandingTheme() {
  const [theme, setTheme] = useState<"light" | "dark">("light")

  useEffect(() => {
    if (localStorage.getItem(STORAGE_KEY) === "dark") setTheme("dark")
  }, [])

  const toggle = () => {
    const next = theme === "light" ? "dark" : "light"
    localStorage.setItem(STORAGE_KEY, next)
    setTheme(next)
  }

  return { theme, toggle }
}

export function ThemeToggle({ theme, onToggle }: { theme: "light" | "dark"; onToggle: () => void }) {
  return (
    <button
      onClick={onToggle}
      aria-label={theme === "light" ? "Switch to dark mode" : "Switch to light mode"}
      className="size-9 rounded-full border border-line text-ink-body hover:text-ink flex items-center justify-center transition-colors"
    >
      {theme === "light" ? <Moon className="size-4" /> : <Sun className="size-4" />}
    </button>
  )
}
