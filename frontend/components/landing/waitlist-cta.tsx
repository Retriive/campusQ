"use client"

import * as React from "react"
import Link from "next/link"
import { ArrowRight, Check } from "lucide-react"
import { API_BASE_URL } from "@/lib/api"

interface WaitlistCtaProps {
  school: string
}

export function WaitlistCta({ school }: WaitlistCtaProps) {
  const [email, setEmail] = React.useState("")
  const [consented, setConsented] = React.useState(false)
  const [joined, setJoined] = React.useState(false)
  const [submitting, setSubmitting] = React.useState(false)
  const [error, setError] = React.useState("")

  if (joined) {
    return (
      <div className="inline-flex items-center gap-2 text-sm text-ink">
        <Check className="size-4 text-primary-ink" />
        You&apos;re on the list — we&apos;ll email you when {school} is ready.
      </div>
    )
  }

  return (
    <form
      onSubmit={async (e) => {
        e.preventDefault()
        if (!email.trim() || !consented || submitting) return
        setSubmitting(true)
        setError("")
        try {
          const fd = new FormData()
          fd.append("email", email.trim())
          fd.append("school", school)
          fd.append("consented", "true")
          const res = await fetch(`${API_BASE_URL}/api/waitlist`, { method: "POST", body: fd })
          const data = await res.json()
          if (data.ok) {
            setJoined(true)
          } else {
            setError(
              data.error === "consent required"
                ? "Please agree to the privacy notice before joining."
                : "That email didn't look right — try again."
            )
          }
        } catch {
          setError("Something went wrong — try again.")
        } finally {
          setSubmitting(false)
        }
      }}
      className="flex flex-col gap-2.5 max-w-lg"
    >
      <div className="flex flex-col sm:flex-row gap-2.5">
        <input
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@school.ca"
          className="text-sm px-4 py-3 rounded-xl border border-line bg-canvas-raised text-ink placeholder:text-ink-faint outline-none focus:border-ink/30 transition-[border-color] duration-200 w-full sm:flex-1"
        />
        <button
          type="submit"
          disabled={submitting || !consented}
          className="land-press inline-flex items-center justify-center gap-2 rounded-xl bg-ink px-5 py-3 text-sm font-semibold text-canvas shrink-0 disabled:opacity-50"
        >
          {submitting ? "Joining…" : "Join waitlist"}
          <ArrowRight className="size-4" />
        </button>
      </div>
      <label className="flex items-start gap-2 text-xs text-ink-faint cursor-pointer">
        <input
          type="checkbox"
          checked={consented}
          onChange={(e) => setConsented(e.target.checked)}
          className="mt-0.5 shrink-0"
          required
        />
        <span>
          I agree to receive emails about CampusQ for {school} and have read the{" "}
          <Link href="/privacy" className="underline underline-offset-2 hover:text-ink">
            Privacy Policy
          </Link>
          .
        </span>
      </label>
      {error && <p className="text-xs text-red-600">{error}</p>}
    </form>
  )
}
