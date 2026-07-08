"use client"

import * as React from "react"
import { useAuth } from "@clerk/nextjs"
import { Plus, X, Sparkles, Loader2, BookOpen } from "lucide-react"
import { Button } from "@/components/ui/button"
import ReactMarkdown from "react-markdown"
import { API_BASE_URL } from "@/lib/api"

export function WhatCanITake() {
  const { getToken } = useAuth()
  const [completed, setCompleted] = React.useState<string[]>([])
  const [input, setInput] = React.useState("")
  const [result, setResult] = React.useState("")
  const [loading, setLoading] = React.useState(false)

  const addCourse = () => {
    const code = input.trim().toUpperCase()
    if (!code || completed.includes(code)) return
    setCompleted((prev) => [...prev, code])
    setInput("")
  }

  const removeCourse = (code: string) => {
    setCompleted((prev) => prev.filter((c) => c !== code))
    setResult("")
  }

  const findEligible = async () => {
    if (completed.length === 0) return
    setLoading(true)
    setResult("")

    const question = `I have completed the following courses: ${completed.join(", ")}. Based on these completed courses, which courses am I now eligible to take? List the courses that have all their prerequisites satisfied by my completed courses. Be specific and list course codes.`

    try {
      const formData = new FormData()
      formData.append("question", question)
      formData.append("history", "[]")

      const token = await getToken().catch(() => null)
      const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
        method: "POST",
        body: formData,
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })

      if (!response.body) throw new Error("No response body")

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ""
      let fullText = ""

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split("\n")
        buffer = lines.pop() || ""

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue
          const jsonStr = line.slice(6)
          if (!jsonStr.trim()) continue
          try {
            const parsed = JSON.parse(jsonStr)
            if (parsed.type === "token") {
              fullText += parsed.content
              setResult(fullText)
            }
          } catch {}
        }
      }
    } catch (e) {
      setResult("Failed to reach the server. Please make sure the backend is running.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-xl font-bold mb-1">What Can I Take Next?</h2>
        <p className="text-sm text-muted-foreground">
          Enter the courses you've already completed, and CampusQ will tell you what you're now eligible to take.
        </p>
      </div>

      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && addCourse()}
          placeholder="Add completed course (e.g. SYSC 2100)"
          className="flex-1 px-4 py-2.5 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
        />
        <Button onClick={addCourse} disabled={!input.trim()} variant="outline" className="gap-2 rounded-xl">
          <Plus className="size-4" />
          Add
        </Button>
      </div>

      {completed.length > 0 && (
        <div>
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">Completed courses</p>
          <div className="flex flex-wrap gap-2">
            {completed.map((code) => (
              <span
                key={code}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-primary/10 text-primary rounded-full text-sm font-mono font-medium"
              >
                {code}
                <button onClick={() => removeCourse(code)} className="hover:text-destructive transition-colors">
                  <X className="size-3" />
                </button>
              </span>
            ))}
          </div>
        </div>
      )}

      <Button
        onClick={findEligible}
        disabled={completed.length === 0 || loading}
        className="gap-2 self-start"
      >
        {loading ? <Loader2 className="size-4 animate-spin" /> : <Sparkles className="size-4" />}
        {loading ? "Searching..." : "Find Eligible Courses"}
      </Button>

      {result && (
        <div className="rounded-xl border border-border bg-secondary/20 p-5">
          <div className="flex items-center gap-2 mb-3 text-sm font-semibold">
            <BookOpen className="size-4 text-primary" />
            Courses you can take now
          </div>
          <div className="prose prose-sm dark:prose-invert max-w-none text-sm leading-relaxed">
            <ReactMarkdown>{result}</ReactMarkdown>
          </div>
        </div>
      )}

      {!result && !loading && completed.length === 0 && (
        <div className="flex flex-col items-center gap-3 py-12 text-center text-muted-foreground">
          <BookOpen className="size-10 opacity-30" />
          <p className="text-sm">Add the courses you've completed to get started.</p>
        </div>
      )}
    </div>
  )
}
