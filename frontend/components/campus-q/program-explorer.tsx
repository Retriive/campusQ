"use client"

import * as React from "react"
import { Loader2, BookOpen, ArrowLeft, Search, ChevronRight, Layers } from "lucide-react"
import { Button } from "@/components/ui/button"
import ReactMarkdown from "react-markdown"
import { cn } from "@/lib/utils"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface Stream {
  label: string      // display name
  queryName: string  // what we send to the backend
}

interface Program {
  name: string
  description: string
  faculty: string
  streams?: Stream[]
}

const FACULTIES: {
  name: string
  color: string
  bgColor: string
  programs: Omit<Program, "faculty">[]
}[] = [
  {
    name: "Engineering & Design",
    color: "text-blue-600 dark:text-blue-400",
    bgColor: "bg-blue-50 dark:bg-blue-950/30",
    programs: [
      {
        name: "Aerospace Engineering",
        description: "Aerodynamics, propulsion, and spacecraft systems",
        streams: [
          { label: "Stream A — Aerodynamics, Propulsion & Vehicle Performance", queryName: "Aerospace Engineering Stream A: Aerodynamics, Propulsion and Vehicle Performance" },
          { label: "Stream B — Aerospace Structures, Systems & Vehicle Design", queryName: "Aerospace Engineering Stream B: Aerospace Structures, Systems and Vehicle Design" },
          { label: "Stream C — Aerospace Electronics & Systems", queryName: "Aerospace Engineering Stream C: Aerospace Electronics and Systems" },
          { label: "Stream D — Space Systems Design", queryName: "Aerospace Engineering Stream D: Space Systems Design" },
        ],
      },
      { name: "Architectural Conservation and Sustainability Engineering", description: "Heritage structures, sustainability, and building technology" },
      { name: "Architecture", description: "Architectural design, history, and building technology" },
      { name: "Biomedical and Electrical Engineering", description: "Engineering applied to medicine — electrical focus" },
      { name: "Biomedical and Mechanical Engineering", description: "Engineering applied to medicine — mechanical focus" },
      { name: "Civil Engineering", description: "Structures, infrastructure, and environmental systems" },
      { name: "Communications Engineering", description: "Wireless systems, networks, and signal processing" },
      { name: "Computer Systems Engineering", description: "Hardware, software, and embedded systems design" },
      { name: "Electrical Engineering", description: "Circuits, power systems, and electromagnetic fields" },
      { name: "Engineering Physics", description: "Physics-based engineering, optics, and quantum systems" },
      { name: "Environmental Engineering", description: "Environmental protection, water, and waste systems" },
      { name: "Industrial Design", description: "Product design, human factors, and manufacturing" },
      { name: "Mechanical Engineering", description: "Mechanics, thermodynamics, and machine design" },
      { name: "Mechatronics Engineering", description: "Mechanical systems, electronics, and control" },
      { name: "Network Technology", description: "Computer networks, security, and telecommunications" },
      {
        name: "Software Engineering",
        description: "Software design, testing, and project management",
        streams: [
          { label: "Software Engineering (General)", queryName: "Software Engineering Bachelor of Engineering" },
          { label: "Stream A — Artificial Intelligence", queryName: "Software Engineering Stream A: Artificial Intelligence" },
        ],
      },
      {
        name: "Sustainable and Renewable Energy Engineering",
        description: "Green energy systems and sustainable design",
        streams: [
          { label: "Stream A — Smart Technologies for Power Generation & Distribution", queryName: "Sustainable and Renewable Energy Engineering Stream A: Smart Technologies for Power Generation and Distribution" },
          { label: "Stream B — Efficient Energy Generation & Conversion", queryName: "Sustainable and Renewable Energy Engineering Stream B: Efficient Energy Generation and Conversion" },
        ],
      },
    ],
  },
  {
    name: "Science",
    color: "text-emerald-600 dark:text-emerald-400",
    bgColor: "bg-emerald-50 dark:bg-emerald-950/30",
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
      { name: "Nanoscience", description: "Materials and phenomena at the nanoscale" },
      { name: "Neuroscience", description: "Brain function, cognition, and nervous system" },
      { name: "Physics", description: "Classical and modern physics, quantum mechanics" },
      { name: "Psychology", description: "Human behaviour, cognition, and mental processes" },
      { name: "Statistics", description: "Statistical theory, data analysis, and probability" },
    ],
  },
  {
    name: "Arts & Social Sciences",
    color: "text-purple-600 dark:text-purple-400",
    bgColor: "bg-purple-50 dark:bg-purple-950/30",
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
    bgColor: "bg-orange-50 dark:bg-orange-950/30",
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
    bgColor: "bg-yellow-50 dark:bg-yellow-950/30",
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
    bgColor: "bg-cyan-50 dark:bg-cyan-950/30",
    programs: [
      { name: "Information Technology (BIT)", description: "IT systems, databases, networking, and software" },
      { name: "Interactive Multimedia and Design", description: "Web, game, and interactive media design" },
    ],
  },
  {
    name: "Health Sciences",
    color: "text-red-500 dark:text-red-400",
    bgColor: "bg-red-50 dark:bg-red-950/30",
    programs: [
      { name: "Health Sciences", description: "Health systems, policy, and interdisciplinary health studies" },
      { name: "Nursing", description: "Collaborative nursing program with health and patient care" },
    ],
  },
]

const ALL_PROGRAMS: Program[] = FACULTIES.flatMap((f) =>
  f.programs.map((p) => ({ ...p, faculty: f.name }))
)

type ViewState =
  | { screen: "directory" }
  | { screen: "streams"; program: Program; faculty: typeof FACULTIES[number] }
  | { screen: "detail"; program: Program; streamLabel?: string; queryName: string }

export function ProgramExplorer() {
  const [view, setView] = React.useState<ViewState>({ screen: "directory" })
  const [result, setResult] = React.useState("")
  const [loading, setLoading] = React.useState(false)
  const [search, setSearch] = React.useState("")

  const loadRequirements = async (queryName: string) => {
    setResult("")
    setLoading(true)
    const question = `What are all the required courses for ${queryName} at Carleton University? Please list them organized by year with course codes and credit values. Include any stream-specific requirements.`
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

  const handleProgramClick = (program: Program) => {
    const faculty = FACULTIES.find((f) => f.name === program.faculty)!
    if (program.streams && program.streams.length > 0) {
      setView({ screen: "streams", program, faculty })
    } else {
      setView({ screen: "detail", program, queryName: program.name })
      loadRequirements(program.name)
    }
  }

  const handleStreamClick = (program: Program, stream: Stream) => {
    setView({ screen: "detail", program, streamLabel: stream.label, queryName: stream.queryName })
    loadRequirements(stream.queryName)
  }

  const goBack = () => {
    if (view.screen === "detail" && (view as any).program?.streams?.length > 0) {
      const program = (view as any).program as Program
      const faculty = FACULTIES.find((f) => f.name === program.faculty)!
      setView({ screen: "streams", program, faculty })
    } else {
      setView({ screen: "directory" })
    }
    setResult("")
  }

  // ── Stream picker ────────────────────────────────────────────────────────
  if (view.screen === "streams") {
    const { program, faculty } = view
    return (
      <div className="flex flex-col gap-6">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => setView({ screen: "directory" })}>
            <ArrowLeft className="size-4" />
          </Button>
          <div>
            <p className={cn("text-xs font-medium mb-0.5", faculty.color)}>{faculty.name}</p>
            <h2 className="text-lg font-semibold">{program.name}</h2>
          </div>
        </div>

        <div className={cn("rounded-xl p-4 border border-border", faculty.bgColor)}>
          <div className="flex items-center gap-2 mb-1">
            <Layers className={cn("size-4", faculty.color)} />
            <p className="text-sm font-semibold">Select your stream</p>
          </div>
          <p className="text-xs text-muted-foreground">
            This program has multiple specialization streams. Each has a different course sequence.
          </p>
        </div>

        <div className="space-y-2">
          {program.streams!.map((stream) => (
            <button
              key={stream.queryName}
              onClick={() => handleStreamClick(program, stream)}
              className="w-full flex items-center justify-between gap-3 px-4 py-3.5 rounded-xl border border-border bg-card hover:bg-secondary/40 hover:border-border/80 transition-all text-left group"
            >
              <span className="text-sm font-medium text-foreground">{stream.label}</span>
              <ChevronRight className="size-3.5 text-muted-foreground/30 shrink-0 group-hover:text-muted-foreground transition-colors" />
            </button>
          ))}
        </div>
      </div>
    )
  }

  // ── Detail view ──────────────────────────────────────────────────────────
  if (view.screen === "detail") {
    const { program, streamLabel } = view as { program: Program; streamLabel?: string; queryName: string }
    const faculty = FACULTIES.find((f) => f.name === program.faculty)
    return (
      <div className="flex flex-col gap-6">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={goBack}>
            <ArrowLeft className="size-4" />
          </Button>
          <div>
            <p className={cn("text-xs font-medium mb-0.5", faculty?.color)}>{program.faculty}</p>
            <h2 className="text-lg font-semibold leading-tight">{program.name}</h2>
            {streamLabel && (
              <p className="text-xs text-muted-foreground mt-0.5">{streamLabel}</p>
            )}
          </div>
        </div>

        {loading && (
          <div className="flex items-center gap-2.5 text-muted-foreground py-8 justify-center text-sm">
            <Loader2 className="size-4 animate-spin" />
            Loading requirements…
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

  // ── Directory ────────────────────────────────────────────────────────────
  const searchResults = search.trim()
    ? ALL_PROGRAMS.filter(
        (p) =>
          p.name.toLowerCase().includes(search.toLowerCase()) ||
          p.description.toLowerCase().includes(search.toLowerCase())
      )
    : null

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-lg font-semibold mb-0.5">Programs</h2>
        <p className="text-sm text-muted-foreground">
          {ALL_PROGRAMS.length} Carleton programs — click any to see requirements
        </p>
      </div>

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

      {searchResults ? (
        <div>
          {searchResults.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">No programs found</p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {searchResults.map((p) => {
                const faculty = FACULTIES.find((f) => f.name === p.faculty)
                return (
                  <ProgramCard key={p.name} program={p} facultyColor={faculty?.color} onClick={() => handleProgramClick(p)} />
                )
              })}
            </div>
          )}
        </div>
      ) : (
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
                    onClick={() => handleProgramClick({ ...p, faculty: faculty.name })}
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
  const hasStreams = !!program.streams?.length
  return (
    <button
      onClick={onClick}
      className="group flex items-center justify-between gap-3 px-4 py-3 rounded-xl border border-border bg-card hover:bg-secondary/40 hover:border-border/80 transition-all text-left"
    >
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-foreground truncate">{program.name}</p>
        <div className="flex items-center gap-2 mt-0.5">
          <p className="text-xs text-muted-foreground truncate">{program.description}</p>
          {hasStreams && (
            <span className={cn(
              "shrink-0 text-[10px] font-semibold px-1.5 py-0.5 rounded-md",
              facultyColor,
              "bg-current/10"
            )}>
              {program.streams!.length} streams
            </span>
          )}
        </div>
      </div>
      <ChevronRight className="size-3.5 text-muted-foreground/30 shrink-0 group-hover:text-muted-foreground transition-colors" />
    </button>
  )
}
