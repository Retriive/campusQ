"use client"

import * as React from "react"
import { X, Send, CheckCircle } from "lucide-react"
import { Button } from "@/components/ui/button"

interface FeedbackModalProps {
  open: boolean
  onClose: () => void
  lastQuery?: string
}

export function FeedbackModal({ open, onClose, lastQuery = "" }: FeedbackModalProps) {
  const [message, setMessage] = React.useState("")
  const [query, setQuery] = React.useState(lastQuery)
  const [submitted, setSubmitted] = React.useState(false)
  const [isLoading, setIsLoading] = React.useState(false)

  React.useEffect(() => {
    setQuery(lastQuery)
  }, [lastQuery])

  React.useEffect(() => {
    if (!open) {
      setTimeout(() => {
        setMessage("")
        setSubmitted(false)
      }, 300)
    }
  }, [open])

  if (!open) return null

  const handleSubmit = async () => {
    if (!message.trim()) return
    setIsLoading(true)
    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
    try {
      const formData = new FormData()
      formData.append("message", message)
      formData.append("query", query)
      await fetch(`${API_URL}/api/feedback`, { method: "POST", body: formData })
      setSubmitted(true)
    } catch {
      setSubmitted(true)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-card border border-border rounded-2xl shadow-2xl w-full max-w-md mx-4 p-6">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-muted-foreground hover:text-foreground transition-colors"
        >
          <X className="size-4" />
        </button>

        {submitted ? (
          <div className="flex flex-col items-center gap-3 py-6 text-center">
            <CheckCircle className="size-10 text-green-500" />
            <h3 className="text-lg font-semibold">Thanks for the feedback!</h3>
            <p className="text-sm text-muted-foreground">Your report helps us improve CampusQ.</p>
            <Button variant="outline" onClick={onClose} className="mt-2">Close</Button>
          </div>
        ) : (
          <>
            <h3 className="text-lg font-semibold mb-1">Report a Problem</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Found an error or missing information? Let us know.
            </p>

            <div className="space-y-3">
              <div>
                <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1 block">
                  What were you searching for? (optional)
                </label>
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="e.g. SYSC 3110 prerequisites"
                  className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1 block">
                  Describe the problem *
                </label>
                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="e.g. The prerequisites listed are wrong, the course description is outdated..."
                  rows={4}
                  className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 resize-none"
                />
              </div>

              <Button
                onClick={handleSubmit}
                disabled={!message.trim() || isLoading}
                className="w-full gap-2"
              >
                <Send className="size-4" />
                {isLoading ? "Sending..." : "Send Report"}
              </Button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
