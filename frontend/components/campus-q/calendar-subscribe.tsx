"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { useCampus } from "./campus-context"
import { CalendarClock, Check, Copy, X } from "lucide-react"
import { API_BASE_URL } from "@/lib/api"

const FEED_URL = `${API_BASE_URL}/api/calendar/deadlines.ics`
const WEBCAL_URL = FEED_URL.replace(/^https?:\/\//, "webcal://")
const FEED_NAME = "Carleton Deadlines (CampusQ)"

// Fire-and-forget adoption telemetry — a failed beacon must never block the UI.
export function trackCalendar(provider: string, action: "add_event" | "subscribe" | "download_all", deadlineId = "") {
  const body = new FormData()
  body.append("provider", provider)
  body.append("action", action)
  body.append("deadline_id", deadlineId)
  fetch(`${API_BASE_URL}/api/calendar/track`, { method: "POST", body, keepalive: true }).catch(() => {})
}

const PROVIDERS: { id: string; label: string; hint: string; href: string }[] = [
  {
    id: "google",
    label: "Google Calendar",
    hint: "Adds the feed to “Other calendars”",
    href: `https://calendar.google.com/calendar/r?cid=${encodeURIComponent(WEBCAL_URL)}`,
  },
  {
    id: "outlook",
    label: "Outlook (school account)",
    hint: "For your @cmail.carleton.ca Microsoft 365 account",
    href: `https://outlook.office.com/calendar/0/addfromweb?url=${encodeURIComponent(FEED_URL)}&name=${encodeURIComponent(FEED_NAME)}`,
  },
  {
    id: "outlook-personal",
    label: "Outlook.com (personal)",
    hint: "For a personal Microsoft account",
    href: `https://outlook.live.com/calendar/0/addfromweb?url=${encodeURIComponent(FEED_URL)}&name=${encodeURIComponent(FEED_NAME)}`,
  },
  {
    id: "webcal",
    label: "Apple Calendar / other apps",
    hint: "Opens as a calendar subscription (webcal)",
    href: WEBCAL_URL,
  },
]

export function CalendarSubscribeModal({ onClose }: { onClose: () => void }) {
  const { theme } = useCampus()
  const [copied, setCopied] = React.useState(false)

  React.useEffect(() => {
    const h = (e: KeyboardEvent) => { if (e.key === "Escape") onClose() }
    window.addEventListener("keydown", h)
    return () => window.removeEventListener("keydown", h)
  }, [onClose])

  const copyUrl = async () => {
    try {
      await navigator.clipboard.writeText(FEED_URL)
      setCopied(true)
      trackCalendar("copy-url", "subscribe")
      setTimeout(() => setCopied(false), 2000)
    } catch { /* clipboard unavailable — the URL is still visible to select */ }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-in fade-in duration-150"
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-md rounded-2xl border border-border bg-card shadow-2xl overflow-hidden animate-in zoom-in-95 duration-150"
      >
        <div className="p-5 border-b border-border/50">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <div className={cn("flex items-center justify-center size-9 rounded-xl text-white shrink-0", theme.bgClass)}>
                <CalendarClock className="size-4" />
              </div>
              <div>
                <p className="text-sm font-semibold text-foreground leading-snug">Sync deadlines to your calendar</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Subscribe once — new and changed dates update automatically.
                </p>
              </div>
            </div>
            <button onClick={onClose} className="text-muted-foreground/40 hover:text-foreground transition-colors">
              <X className="size-4" />
            </button>
          </div>
        </div>

        <div className="p-5 flex flex-col gap-2">
          {PROVIDERS.map((p) => (
            <a
              key={p.id}
              href={p.href}
              target={p.id === "webcal" ? undefined : "_blank"}
              rel="noopener noreferrer"
              onClick={() => trackCalendar(p.id, "subscribe")}
              className="flex items-center justify-between gap-3 px-3.5 py-3 rounded-xl border border-border hover:bg-secondary/50 hover:border-border/80 transition-colors text-left"
            >
              <div className="min-w-0">
                <p className="text-sm font-medium text-foreground">{p.label}</p>
                <p className="text-[11px] text-muted-foreground mt-0.5">{p.hint}</p>
              </div>
              <span className="text-xs text-muted-foreground/60 shrink-0">→</span>
            </a>
          ))}

          {/* Manual fallback — every calendar app accepts a feed URL */}
          <div className="mt-2 flex items-center gap-2">
            <code className="flex-1 min-w-0 truncate text-[11px] text-muted-foreground bg-secondary/60 border border-border/60 rounded-lg px-2.5 py-2">
              {FEED_URL}
            </code>
            <button
              onClick={copyUrl}
              className="shrink-0 inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-2 rounded-lg border border-border text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
            >
              {copied ? <Check className="size-3.5 text-success" /> : <Copy className="size-3.5" />}
              {copied ? "Copied" : "Copy"}
            </button>
          </div>
          <p className="text-[11px] text-muted-foreground/60 leading-relaxed">
            Each deadline arrives as an all-day event with a reminder 2 days before.
            Remove the subscription any time from your calendar’s settings.
          </p>
        </div>
      </div>
    </div>
  )
}
