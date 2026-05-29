"use client"

import * as React from "react"
import { Loader2, BookOpen, ArrowLeft, Search, ChevronRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import ReactMarkdown from "react-markdown"
import { cn } from "@/lib/utils"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface Program {
  name: string
  faculty: string
  description: string
}

const FACULTIES: { name: string; color: string; programs: Omit<Program, "faculty">[] }[] = [
  {
    name: "Engineering & Design",
    color: "text-blue-600 dark:text-blue-400",
    programs: [
      { name: "Aerospace Engineering", description: "Aerodynamics, propulsion, and spacecraft systems" },
      { name: "Architecture", description: "Architectural design, history, and building technology" },
      { name: "Biomedical and Electrical Engineering", description: "Engineering principles applied to medicine and biology" },
      { name: "Civil Engineering", description: "Structures, infrastructure, and environmental systems" },
      { name: "Communications Engineering", description: "Wireless systems, networks, and signal processing" },
      { name: "Computer Systems Engineering", description: "Hardware, software, and embedded systems design" },
      { name: "Electrical Engineering", description: "Circuits, power systems, and electromagnetic fields" },
      { name: "Industrial Design", description: "Product design, human factors, and manufacturing" },
      { name: "Mechanical Engineering", description: "Mechanics, thermodynamics, and machine design" },
      { name: "Network Technology", description: "Computer networks, security, and telecommunications" },
      { name: "Software Engineering", description: "Software design, testing, and project management" },
      { name: "Sustainable and Renewable Energy Engineering", description: "Green energy systems and sustainable design" },
    ],
  },
  {
    name: "Science",
    color: "text-emerald-600 dark:text-emerald-400",
    programs: [
      { name: "Biochemistry", description: "Chemistry of biological processes and living systems" },
      { name: "Bioinformatics", description: "Computational approaches to biological data" },
      { name: "Biology", description: "Life sciences from molecular to ecosystem level" },
      { name: "Chemistry", description: "Molecular structure, reactions, and materials" },
      { name: "Computer Mathematics", description: "Mathematics and computing combined" },
      { name: "Computer Science", description: "Algorithms, AI, software, and theory of computation" },
      { name: "Data Science", description: "Statistics, machine learning, and big data analysis" },
      { name: "Earth Sciences", description: "Geology, geophysics, and earth systems" },
      { name: "Environmental Science", description: "Environmental systems, ecology, and sustainability" },
      { name: "Food Science and Nutrition", description: "Food chemistry, safety, and human nutrition" },
      { name: "Mathematics", description: "Pure and applied mathematics" },
      { name: "Neuroscience", description: "Brain function, cognition, and nervous system" },
      { name: "Physics", description: "Classical and modern physics, quantum mechanics" },
      { name: "Psychology", description: "Human behaviour, cognition, and mental processes" },
      { name: "Statistics", description: "Statistical theory, data analysis, and probability" },
    ],
  },
  {
    name: "Arts & Social Sciences",
    color: "text-purple-600 dark:text-purple-400",
    programs: [
      { name: "Anthropology", description: "Human cultures, evolution, and social organization" },
      { name: "Art History", description: "Visual arts, architecture, and cultural heritage" },
      { name: "Canadian Studies", description: "Canadian history, culture, politics, and society" },
      { name: "Cognitive Science", description: "Mind, intelligence, and information processing" },
      { name: "Communication and Media Studies", description: "Media theory, journalism, and digital communication" },
      { name: "Criminology and Criminal Justice", description: "Crime, law, and the justice system" },
      { name: "Economics", description: "Microeconomics, macroeconomics, and economic policy" },
      { name: "English Language and Literature", description: "Literary analysis, writing, and cultural criticism" },
      { name: "Environmental Studies", description: "Environmental policy, sustainability, and society" },
      { name: "Film Studies", description: "Film theory, history, and production" },
      { name: "French", description: "French language, literature, and francophone cultures" },
      { name: "Geography", description: "Physical and human geography, GIS, and spatial analysis" },
      { name: "Global and International Studies", description: "International relations, global politics, and development" },
      { name: "History", description: "Historical analysis from ancient to contemporary" },
      { name: "Indigenous Studies", description: "Indigenous histories, cultures, and contemporary issues" },
      { name: "Journalism", description: "News writing, reporting, and digital media" },
      { name: "Law and Legal Studies", description: "Legal theory, justice systems, and policy" },
      { name: "Linguistics", description: "Language structure, acquisition, and cognitive linguistics" },
      { name: "Music", description: "Music theory, performance, history, and composition" },
      { name: "Philosophy", description: "Ethics, logic, metaphysics, and epistemology" },
      { name: "Political Science", description: "Political theory, government, and international relations" },
      { name: "Religion", description: "World religions, theology, and religious studies" },
      { name: "Sociology", description: "Social structures, inequality, and human society" },
      { name: "Women's and Gender Studies", description: "Gender, feminism, and social justice" },
    ],
  },
  {
    name: "Sprott School of Business",
    color: "text-orange-600 dark:text-orange-400",
    programs: [
      { name: "Accounting", description: "Financial reporting, auditing, and taxation" },
      { name: "Business (BCom)", description: "Core business fundamentals across all disciplines" },
      { name: "Finance", description: "Investment, financial markets, and corporate finance" },
      { name: "Human Resources Management", description: "People management, organizational behaviour" },
      { name: "International Business", description: "Global trade, multinational strategy" },
      { name: "Management", description: "Organizational leadership, strategy, and operations" },
      { name: "Marketing", description: "Consumer behaviour, branding, and digital marketing" },
      { name: "Supply Chain Management", description: "Logistics, procurement, and operations" },
    ],
  },
  {
    name: "Public Affairs",
    color: "text-yellow-600 dark:text-yellow-500",
    programs: [
      { name: "Human Rights", description: "International human rights law and advocacy" },
      { name: "Public Administration", description: "Government management, policy, and public service" },
      { name: "Public Affairs and Policy Management", description: "Policy analysis, advocacy, and government relations" },
      { name: "Social Work", description: "Social services, community development, and welfare policy" },
    ],
  },
  {
    name: "Information Technology",
    color: "text-cyan-600 dark:text-cyan-400",
    programs: [
      { name: "Information Technology (BIT)", description: "IT systems, databases, networking, and software" },
      { name: "Interactive Multimedia and Design", description: "Web, game, and interactive media design" },
    ],
  },
  {
    name: "Health Sciences",
    color: "text-red-600 dark:text-red-400",
    programs: [
      { name: "Health Sciences", description: "Health systems, policy, and interdisciplinary health studies" },
    ],
  },
]

const ALL_PROGRAMS: Program[] = FACULTIES.flatMap((f) =>
  f.programs.map((p) => ({ ...p, faculty: f.name }))
)

export function ProgramExplorer() {
  const [selected, setSelected] = React.useState<Program | null>(null)
  const [result, setResult] = React.useState("")
  const [loading, setLoading] = React.useState(false)
  const [search, setSearch] = React.useState("")

  const searchResults = search.trim()
    ? ALL_PROGRAMS.filter(
        (p) =>
          p.name.toLowerCase().includes(search.toLowerCase()) ||
          p.description.toLowerCase().includes(search.toLowerCase())
      )
    : null

  const loadProgram = async (program: Program) => {
    setSelected(program)
    setResult("")
    setLoading(true)

    const question = `What are all the required courses for the ${program.name} program at Carleton University? List them organized by year with course codes and credit values.`

    try {
      const formData = new FormData()
      formData.append("question", question)
      formData.append("history", "[]")

      const response = await fetch(`${API_URL}/api/chat/stream`, { method: "POST", body: formData })
      if (!response.body) throw new Error()

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
          try {
            const parsed = JSON.parse(line.slice(6))
            if (parsed.type === "token") { fullText += parsed.content; setResult(fullText) }
          } catch {}
        }
      }
    } catch {
      setResult("Failed to load. Make sure the backend is running.")
    } finally {
      setLoading(false)
    }
  }

  // Detail view
  if (selected) {
    const faculty = FACULTIES.find((f) => f.name === selected.faculty)
    return (
      <div className="flex flex-col gap-6">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => { setSelected(null); setResult("") }}>
            <ArrowLeft className="size-4" />
          </Button>
          <div>
            <p className={cn("text-xs font-medium mb-0.5", faculty?.color)}>{selected.faculty}</p>
            <h2 className="text-lg font-semibold leading-tight">{selected.name}</h2>
          </div>
        </div>

        {loading && (
          <div className="flex items-center gap-2.5 text-muted-foreground py-8 justify-center text-sm">
            <Loader2 className="size-4 animate-spin" />
            Loading program requirements…
          </div>
        )}

        {result && (
          <div className="rounded-xl border border-border bg-card p-5">
            <div className="flex items-center gap-2 mb-4 text-sm font-medium">
              <BookOpen className="size-4 text-primary" />
              Course Requirements
            </div>
            <div className="prose prose-sm dark:prose-invert max-w-none text-sm leading-relaxed">
              <ReactMarkdown>{result}</ReactMarkdown>
            </div>
          </div>
        )}
      </div>
    )
  }

  // Directory view
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-lg font-semibold mb-0.5">Programs</h2>
        <p className="text-sm text-muted-foreground">{ALL_PROGRAMS.length} Carleton programs — click any to see requirements</p>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-3.5 text-muted-foreground" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search programs…"
          className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-border bg-card text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 placeholder:text-muted-foreground/50"
        />
      </div>

      {/* Search results */}
      {searchResults ? (
        <div>
          {searchResults.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">No programs found</p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {searchResults.map((p) => {
                const faculty = FACULTIES.find((f) => f.name === p.faculty)
                return (
                  <ProgramCard
                    key={p.name}
                    program={p}
                    facultyColor={faculty?.color}
                    onClick={() => loadProgram(p)}
                  />
                )
              })}
            </div>
          )}
        </div>
      ) : (
        /* Grouped by faculty */
        <div className="space-y-8">
          {FACULTIES.map((faculty) => (
            <div key={faculty.name}>
              <div className="flex items-center gap-2 mb-3">
                <h3 className={cn("text-xs font-semibold uppercase tracking-widest", faculty.color)}>
                  {faculty.name}
                </h3>
                <span className="text-xs text-muted-foreground/40">({faculty.programs.length})</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {faculty.programs.map((p) => (
                  <ProgramCard
                    key={p.name}
                    program={{ ...p, faculty: faculty.name }}
                    facultyColor={faculty.color}
                    onClick={() => loadProgram({ ...p, faculty: faculty.name })}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function ProgramCard({
  program,
  facultyColor,
  onClick,
}: {
  program: Program
  facultyColor?: string
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className="group flex items-center justify-between gap-3 px-4 py-3 rounded-xl border border-border bg-card hover:bg-secondary/40 hover:border-border/80 transition-all text-left"
    >
      <div className="min-w-0">
        <p className="text-sm font-medium text-foreground truncate">{program.name}</p>
        <p className="text-xs text-muted-foreground truncate mt-0.5">{program.description}</p>
      </div>
      <ChevronRight className="size-3.5 text-muted-foreground/30 shrink-0 group-hover:text-muted-foreground transition-colors" />
    </button>
  )
}
