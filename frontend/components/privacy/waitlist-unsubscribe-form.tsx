"use client"

import * as React from "react"
import { API_BASE_URL } from "@/lib/api"

export function WaitlistUnsubscribeForm() {
  const [email, setEmail] = React.useState("")
  const [submitting, setSubmitting] = React.useState(false)
  const [done, setDone] = React.useState(false)
  const [removed, setRemoved] = React.useState(0)
  const [error, setError] = React.useState("")

  if (done) {
    return (
      <p className="text-sm text-muted-foreground">
        {removed > 0
          ? `Removed ${removed} waitlist entr${removed === 1 ? "y" : "ies"} for that email.`
          : "No waitlist entry found for that email — you're clear."}
      </p>
    )
  }

  return (
    <form
      className="flex flex-col gap-2 not-prose max-w-md"
      onSubmit={async (e) => {
        e.preventDefault()
        if (!email.trim() || submitting) return
        setSubmitting(true)
        setError("")
        try {
          const fd = new FormData()
          fd.append("email", email.trim())
          const res = await fetch(`${API_BASE_URL}/api/waitlist/unsubscribe`, {
            method: "POST",
            body: fd,
          })
          const data = await res.json().catch(() => ({}))
          if (!res.ok || data.ok === false) {
            setError("That email didn't look right — try again.")
            return
          }
          setRemoved(Number(data.removed) || 0)
          setDone(true)
        } catch {
          setError("Something went wrong — try again.")
        } finally {
          setSubmitting(false)
        }
      }}
    >
      <div className="flex flex-wrap gap-2">
        <input
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@school.ca"
          className="text-sm px-3 py-2 rounded-md border border-border bg-background flex-1 min-w-[12rem]"
        />
        <button
          type="submit"
          disabled={submitting}
          className="text-sm font-medium px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
        >
          {submitting ? "Removing…" : "Unsubscribe"}
        </button>
      </div>
      {error && <p className="text-xs text-red-500">{error}</p>}
    </form>
  )
}
