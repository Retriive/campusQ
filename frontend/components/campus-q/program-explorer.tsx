"use client"

import * as React from "react"
import { ChevronRight, Loader2, BookOpen, GraduationCap, ArrowLeft } from "lucide-react"
import { Button } from "@/components/ui/button"
import ReactMarkdown from "react-markdown"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface Program {
  name: string
  faculty: string
  description: string
}

const PROGRAMS: Program[] = [
  { name: "Computer Systems Engineering", faculty: "Engineering", description: "Hardware, software, and embedded systems" },
  { name: "Software Engineering", faculty: "Engineering", description: "Software design, testing, and project management" },
  { name: "Electrical Engineering", faculty: "Engineering", description: "Circuits, signals, and power systems" },
  { name: "Mechanical Engineering", faculty: "Engineering", description: "Mechanics, thermodynamics, and design" },
  { name: "Civil Engineering", faculty: "Engineering", description: "Structures, infrastructure, and environmental systems" },
  { name: "Aerospace Engineering", faculty: "Engineering", description: "Aerodynamics, propulsion, and spacecraft" },
  { name: "Biomedical and Electrical Engineering", faculty: "Engineering", description: "Engineering applied to medicine and biology" },
  { name: "Sustainable and Renewable Energy Engineering", faculty: "Engineering", description: "Green energy systems and sustainability" },
  { name: "Communications Engineering", faculty: "Engineering", description: "Wireless, networks, and signal processing" },
  { name: "Network Technology", faculty: "Engineering", description: "Computer networks and cybersecurity" },
  { name: "Computer Science", faculty: "Science", description: "Algorithms, AI, software, and theory of computation" },
  { name: "Mathematics", faculty: "Science", description: "Pure and applied mathematics" },
  { name: "Physics", faculty: "Science", description: "Classical and modern physics" },
  { name: "Data Science", faculty: "Science", description: "Statistics, machine learning, and big data" },
  { name: "Information Technology", faculty: "Science", description: "IT systems, databases, and networks" },
]

const FACULTY_COLORS: Record<string, string> = {
  Engineering: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
  Science: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
  Business: "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400",
}

export function ProgramExplorer() {
  const [selected, setSelected] = React.useState<Program | null>(null)
  const [result, setResult] = React.useState("")
  const [loading, setLoading] = React.useState(false)

  const loadProgram = async (program: Program) => {
    setSelected(program)
    setResult("")
    setLoading(true)

    const question = `What are all the required courses for the ${program.name} program at Carleton University? List the required courses organized by year, including course codes, credit values, and any important notes about electives or streams.`

    try {
      const formData = new FormData()
      formData.append("question", question)
      formData.append("history", "[]")

      const response = await fetch(`${API_URL}/api/chat/stream`, {
        method: "POST",
        body: formData,
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
    } catch {
      setResult("Failed to load program requirements. Please make sure the backend is running.")
    } finally {
      setLoading(false)
    }
  }

  const faculties = [...new Set(PROGRAMS.map((p) => p.faculty))]

  return (
    <div className="flex flex-col gap-6">
      {!selected ? (
        <>
          <div>
            <h2 className="text-xl font-bold mb-1">Program Explorer</h2>
            <p className="text-sm text-muted-foreground">
              Browse Carleton programs and see their full course requirements.
            </p>
          </div>

          {faculties.map((faculty) => (
            <div key={faculty}>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
                {faculty}
              </h3>
              <div className="space-y-2">
                {PROGRAMS.filter((p) => p.faculty === faculty).map((program) => (
                  <button
                    key={program.name}
                    onClick={() => loadProgram(program)}
                    className="w-full flex items-center justify-between gap-3 p-4 rounded-xl border border-border bg-card/50 hover:bg-card hover:border-primary/40 transition-all text-left group"
                  >
                    <div className="flex items-start gap-3">
                      <GraduationCap className="size-5 text-primary mt-0.5 shrink-0" />
                      <div>
                        <p className="font-medium text-sm text-foreground">{program.name}</p>
                        <p className="text-xs text-muted-foreground mt-0.5">{program.description}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${FACULTY_COLORS[faculty] || "bg-secondary text-secondary-foreground"}`}>
                        {faculty}
                      </span>
                      <ChevronRight className="size-4 text-muted-foreground group-hover:text-primary transition-colors" />
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ))}
        </>
      ) : (
        <>
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => { setSelected(null); setResult("") }}
              className="shrink-0"
            >
              <ArrowLeft className="size-4" />
            </Button>
            <div>
              <h2 className="text-xl font-bold">{selected.name}</h2>
              <p className="text-sm text-muted-foreground">{selected.faculty}</p>
            </div>
          </div>

          {loading && (
            <div className="flex items-center gap-3 text-muted-foreground py-8 justify-center">
              <Loader2 className="size-5 animate-spin" />
              <span className="text-sm">Loading program requirements...</span>
            </div>
          )}

          {result && (
            <div className="rounded-xl border border-border bg-secondary/20 p-5">
              <div className="flex items-center gap-2 mb-3 text-sm font-semibold">
                <BookOpen className="size-4 text-primary" />
                Program Requirements
              </div>
              <div className="prose prose-sm dark:prose-invert max-w-none text-sm leading-relaxed">
                <ReactMarkdown>{result}</ReactMarkdown>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
