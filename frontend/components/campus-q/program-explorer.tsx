"use client"

import * as React from "react"
import { Loader2, BookOpen, ArrowLeft, Search, ChevronRight, Layers, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import ReactMarkdown from "react-markdown"
import { cn } from "@/lib/utils"
import { useCampus } from "./campus-context"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface Stream {
  label: string
  queryName: string
}

interface Program {
  name: string
  description: string
  faculty: string
  streams?: Stream[]
}

const FACULTIES: {
  name: string
  short: string
  color: string
  bgColor: string
  dotColor: string
  programs: Omit<Program, "faculty">[]
}[] = [
  {
    name: "Engineering & Design",
    short: "Eng",
    color: "text-blue-600 dark:text-blue-400",
    bgColor: "bg-blue-500",
    dotColor: "bg-blue-500",
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
    short: "Sci",
    color: "text-emerald-600 dark:text-emerald-400",
    bgColor: "bg-emerald-500",
    dotColor: "bg-emerald-500",
    programs: [
      { name: "Biochemistry", description: "Chemistry of biological processes and living systems" },
      { name: "Bioinformatics", description: "Computational approaches to biological data" },
      { name: "Biology", description: "Life sciences from molecular to ecosystem level" },
      { name: "Chemistry", description: "Molecular structure, reactions, and materials" },
      { name: "Computer Mathematics", description: "Mathematics and computing combined" },
      {
        name: "Computer Science",
        description: "Algorithms, AI, software, and theory of computation",
        streams: [
          { label: "B.C.S. Honours (General)", queryName: "Computer Science B.C.S. Honours" },
          { label: "Algorithms Stream", queryName: "Computer Science Algorithms Stream B.C.S. Honours" },
          { label: "AI & Machine Learning Stream", queryName: "Computer Science Artificial Intelligence and Machine Learning Stream B.C.S. Honours" },
          { label: "Computer Game Development Stream", queryName: "Computer Science Computer Game Development Stream B.C.S. Honours" },
          { label: "Cybersecurity Stream", queryName: "Computer Science Cybersecurity Stream B.C.S. Honours" },
          { label: "Management & Business Systems Stream", queryName: "Computer Science Management and Business Systems Stream B.C.S. Honours" },
          { label: "Software Engineering Stream", queryName: "Computer Science Software Engineering Stream B.C.S. Honours" },
          { label: "UX/UI Stream", queryName: "Computer Science User Experience and User Interfaces Stream B.C.S. Honours" },
          { label: "B.C.S. Major", queryName: "Computer Science B.C.S. Major" },
          { label: "Combined Honours — Computing Theory & Numerical Methods", queryName: "Computer Science and Mathematics Concentration in Computing Theory and Numerical Methods B.Math. Combined Honours" },
          { label: "Combined Honours — Statistics & Computing", queryName: "Computer Science and Mathematics Concentration in Statistics and Computing B.Math. Combined Honours" },
          { label: "Cybersecurity B.Cyber. Honours", queryName: "Cybersecurity B.Cyber. Honours" },
          { label: "Minor in Computer Science", queryName: "Minor in Computer Science" },
        ],
      },
      { name: "Data Science", description: "Statistics, machine learning, and big data analysis" },
      {
        name: "Earth Sciences",
        description: "Geology, geophysics, and earth systems",
        streams: [
          { label: "B.Sc. Honours", queryName: "Earth Sciences B.Sc. Honours" },
          { label: "B.Sc. Honours — Concentration in Environmental Geosciences", queryName: "Earth Sciences with Concentration in Environmental Geosciences B.Sc. Honours" },
          { label: "B.Sc. Major", queryName: "Earth Sciences B.Sc. Major" },
          { label: "B.Sc.", queryName: "Earth Sciences B.Sc." },
          { label: "Vertebrate Paleontology and Paleoecology — B.Sc. Honours", queryName: "Earth Sciences in Vertebrate Paleontology and Paleoecology B.Sc. Honours" },
          { label: "Vertebrate Paleontology and Paleoecology — B.Sc. Major", queryName: "Earth Sciences in Vertebrate Paleontology and Paleoecology B.Sc. Major" },
          { label: "Combined Honours — Earth Sciences and Physical Geography", queryName: "Earth Sciences and Physical Geography B.Sc. Combined Honours" },
          { label: "Combined Honours — Biology and Earth Sciences", queryName: "Biology and Earth Sciences B.Sc. Combined Honours" },
          { label: "Combined Honours — Chemistry and Earth Sciences", queryName: "Chemistry and Earth Sciences B.Sc. Combined Honours" },
          { label: "Minor in Earth Sciences", queryName: "Minor in Earth Sciences: Earth Resources and Processes" },
        ],
      },
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
    short: "Arts",
    color: "text-purple-600 dark:text-purple-400",
    bgColor: "bg-purple-500",
    dotColor: "bg-purple-500",
    programs: [
      { name: "Anthropology", description: "Human cultures, evolution, and social organization" },
      { name: "Art History", description: "Visual arts, architecture, and cultural heritage" },
      { name: "Canadian Studies", description: "Canadian history, culture, politics, and society" },
      { name: "Cognitive Science", description: "Mind, intelligence, and information processing" },
      {
        name: "Communication and Media Studies",
        description: "Media theory, journalism, and digital communication",
        streams: [
          { label: "B.Co.M.S. Honours", queryName: "Communication and Media Studies B.Co.M.S. Honours" },
          { label: "B.Co.M.S. Honours — Concentration in Government and Professional Communication", queryName: "Concentration in Government and Professional Communication" },
          { label: "B.Co.M.S. Honours — Concentration in Media and Entertainment Industries", queryName: "Concentration in Media and Entertainment Industries" },
          { label: "B.Co.M.S. Honours — Concentration in Public Engagement and Civic Culture", queryName: "Concentration in Public Engagement and Civic Culture" },
          { label: "B.Co.M.S. Combined Honours", queryName: "Communication and Media Studies B.Co.M.S. Combined Honours" },
          { label: "B.Co.M.S. (General)", queryName: "Communication and Media Studies B.Co.M.S." },
          { label: "Specialization in Global Media and Communication — B.G.In.S. Honours", queryName: "Specialization in Global Media and Communication B.G.In.S. Honours" },
          { label: "Stream in Global Media and Communication — B.G.In.S.", queryName: "Stream in Global Media and Communication B.G.In.S." },
          { label: "Minor in Communication and Media Studies", queryName: "Minor in Communication and Media Studies" },
          { label: "Journalism and Communication and Media Studies B.J. Combined Honours", queryName: "Journalism and Communication and Media Studies B.J. Combined Honours" },
        ],
      },
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
    name: "Sprott Business",
    short: "Biz",
    color: "text-orange-600 dark:text-orange-400",
    bgColor: "bg-orange-500",
    dotColor: "bg-orange-500",
    programs: [
      {
        name: "Accounting",
        description: "Financial reporting, auditing, and taxation",
        streams: [
          { label: "Bachelor of Accounting Honours", queryName: "Bachelor of Accounting Honours" },
          { label: "Post-Baccalaureate Diploma in Accounting", queryName: "Post-Baccalaureate Diploma in Accounting" },
        ],
      },
      {
        name: "Business (BCom)",
        description: "Core business fundamentals across all disciplines",
        streams: [
          { label: "B.Com. Honours (General)", queryName: "Bachelor of Commerce Honours" },
          { label: "B.Com. Honours — Concentration in Accounting", queryName: "Concentration in Accounting" },
          { label: "B.Com. Honours — Concentration in Business Analytics", queryName: "Concentration in Business Analytics" },
          { label: "B.Com. Honours — Concentration in Entrepreneurship", queryName: "Concentration in Entrepreneurship" },
          { label: "B.Com. Honours — Concentration in Finance", queryName: "Concentration in Finance" },
          { label: "B.Com. Honours — Concentration in Information Systems", queryName: "Concentration in Information Systems" },
          { label: "B.Com. Honours — Concentration in International Business", queryName: "Concentration in International Business" },
          { label: "B.Com. Honours — Concentration in Management", queryName: "Concentration in Management" },
          { label: "B.Com. Honours — Concentration in Marketing", queryName: "Concentration in Marketing" },
          { label: "B.Com. Honours — Concentration in Supply Chain Management", queryName: "Concentration in Supply Chain Management" },
          { label: "Bachelor of Commerce (Non-Honours)", queryName: "Bachelor of Commerce" },
          { label: "Minor in Business", queryName: "Minor in Business" },
          { label: "Minor in Business (for Bachelor of Engineering)", queryName: "Minor in Business for Bachelor of Engineering" },
          { label: "Minor in Arts Management", queryName: "Minor in Arts Management" },
        ],
      },
      {
        name: "Finance",
        description: "Investment, financial markets, and corporate finance",
        streams: [
          { label: "B.Com. Honours — Concentration in Finance", queryName: "Concentration in Finance" },
          { label: "Stream in Corporate Finance", queryName: "Stream in Corporate Finance" },
          { label: "Stream in Investments", queryName: "Stream in Investments" },
          { label: "Stream in Financial Planning", queryName: "Stream in Financial Planning" },
          { label: "Minor in Business (Finance)", queryName: "Minor in Business (Finance)" },
        ],
      },
      {
        name: "Human Resources Management",
        description: "People management, organizational behaviour",
        streams: [
          { label: "B.Com. Honours — Concentration in Management", queryName: "Concentration in Management" },
          { label: "Minor in Human Resources and Management (for B.A. Psychology Honours)", queryName: "Minor in Human Resources and Management for B.A. Honours Psychology" },
        ],
      },
      {
        name: "International Business",
        description: "Global trade, multinational strategy",
        streams: [
          { label: "Bachelor of International Business Honours", queryName: "Bachelor of International Business Honours" },
          { label: "B.Com. Honours — Concentration in International Business", queryName: "Concentration in International Business" },
          { label: "Stream in International Business (B.Acc / B.Com)", queryName: "Stream in International Business" },
          { label: "Stream in International Management (B.Acc / B.Com)", queryName: "Stream in International Management" },
          { label: "Minor in Business (International Business)", queryName: "Minor in Business (International Business)" },
        ],
      },
      {
        name: "Management",
        description: "Organizational leadership, strategy, and operations",
        streams: [
          { label: "B.Com. Honours — Concentration in Management", queryName: "Concentration in Management" },
          { label: "Stream in Entrepreneurship", queryName: "Stream in Entrepreneurship" },
          { label: "Stream in Sustainability", queryName: "Stream in Sustainability" },
          { label: "Minor in Business (Entrepreneurship)", queryName: "Minor in Business (Entrepreneurship)" },
          { label: "Minor in Business (Sustainability)", queryName: "Minor in Business (Sustainability)" },
        ],
      },
      {
        name: "Marketing",
        description: "Consumer behaviour, branding, and digital marketing",
        streams: [
          { label: "B.Com. Honours — Concentration in Marketing", queryName: "Concentration in Marketing" },
          { label: "Stream in Marketing", queryName: "Stream in Marketing" },
          { label: "Minor in Business (Marketing)", queryName: "Minor in Business (Marketing)" },
        ],
      },
      {
        name: "Supply Chain Management",
        description: "Logistics, procurement, and operations",
        streams: [
          { label: "B.Com. Honours — Concentration in Supply Chain Management", queryName: "Concentration in Supply Chain Management" },
          { label: "Stream in Supply Chain Management", queryName: "Stream in Supply Chain Management" },
          { label: "Stream in Business Analytics", queryName: "Stream in Business Analytics" },
          { label: "Stream in Information Systems", queryName: "Stream in Information Systems" },
          { label: "Minor in Business (Supply Chain Management)", queryName: "Minor in Business (Supply Chain Management)" },
          { label: "Minor in Business (Information Systems)", queryName: "Minor in Business (Information Systems)" },
        ],
      },
    ],
  },
  {
    name: "Public Affairs",
    short: "PA",
    color: "text-yellow-600 dark:text-yellow-500",
    bgColor: "bg-yellow-500",
    dotColor: "bg-yellow-500",
    programs: [
      { name: "Human Rights", description: "International human rights law and advocacy" },
      { name: "Public Administration", description: "Government management, policy, and public service" },
      { name: "Public Affairs and Policy Management", description: "Policy analysis, advocacy, and government relations" },
      { name: "Social Work", description: "Social services, community development, and welfare policy" },
    ],
  },
  {
    name: "Information Technology",
    short: "IT",
    color: "text-cyan-600 dark:text-cyan-400",
    bgColor: "bg-cyan-500",
    dotColor: "bg-cyan-500",
    programs: [
      { name: "Information Technology (BIT)", description: "IT systems, databases, networking, and software" },
      { name: "Interactive Multimedia and Design", description: "Web, game, and interactive media design" },
    ],
  },
  {
    name: "Health Sciences",
    short: "Health",
    color: "text-red-500 dark:text-red-400",
    bgColor: "bg-red-500",
    dotColor: "bg-red-500",
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
  const { theme } = useCampus()
  const [view, setView] = React.useState<ViewState>({ screen: "directory" })
  const [result, setResult] = React.useState("")
  const [loading, setLoading] = React.useState(false)
  const [search, setSearch] = React.useState("")
  const [activeFaculty, setActiveFaculty] = React.useState<string>("All")

  const loadRequirements = async (queryName: string) => {
    setResult("")
    setLoading(true)
    const question = `What are all the required courses for ${queryName} at Carleton University? Please list them organized by year with course codes and credit values. Include any stream-specific requirements.`
    try {
      const formData = new FormData()
      formData.append("question", question)
      formData.append("history", "[]")
      formData.append("session_id", "program-explorer")
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
    if (view.screen === "detail") {
      const program = (view as { program: Program }).program
      if (program.streams && program.streams.length > 0) {
        const faculty = FACULTIES.find((f) => f.name === program.faculty)!
        setView({ screen: "streams", program, faculty })
        setResult("")
        return
      }
    }
    setView({ screen: "directory" })
    setResult("")
  }

  // ── Stream picker ─────────────────────────────────────────────────────────
  if (view.screen === "streams") {
    const { program, faculty } = view
    return (
      <div className="flex flex-col gap-5">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => { setView({ screen: "directory" }); setResult("") }}>
            <ArrowLeft className="size-4" />
          </Button>
          <div>
            <div className="flex items-center gap-2 mb-0.5">
              <span className={cn("text-[10px] font-semibold uppercase tracking-widest", faculty.color)}>
                {faculty.name}
              </span>
            </div>
            <h2 className="text-lg font-semibold leading-tight">{program.name}</h2>
          </div>
        </div>

        <div className={cn("rounded-xl p-4 border border-border/50", `bg-${faculty.bgColor.split("-")[1]}-500/5`)}>
          <div className="flex items-center gap-2 mb-1">
            <Layers className={cn("size-4", faculty.color)} />
            <p className="text-sm font-semibold">Select degree or option</p>
          </div>
          <p className="text-xs text-muted-foreground">
            {program.streams!.length} options available — Honours, Combined, Minors, and more.
          </p>
        </div>

        <div className="space-y-1.5">
          {program.streams!.map((stream) => (
            <button
              key={stream.queryName}
              onClick={() => handleStreamClick(program, stream)}
              className="w-full flex items-center justify-between gap-3 px-4 py-3 rounded-xl border border-border bg-card hover:bg-secondary/40 hover:border-border/60 transition-all text-left group"
            >
              <span className="text-sm text-foreground">{stream.label}</span>
              <ChevronRight className="size-3.5 text-muted-foreground/30 shrink-0 group-hover:text-muted-foreground transition-colors" />
            </button>
          ))}
        </div>
      </div>
    )
  }

  // ── Detail view ───────────────────────────────────────────────────────────
  if (view.screen === "detail") {
    const { program, streamLabel } = view as { program: Program; streamLabel?: string; queryName: string }
    const faculty = FACULTIES.find((f) => f.name === program.faculty)
    return (
      <div className="flex flex-col gap-5">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={goBack}>
            <ArrowLeft className="size-4" />
          </Button>
          <div className="flex-1 min-w-0">
            <p className={cn("text-[10px] font-semibold uppercase tracking-widest mb-0.5", faculty?.color)}>
              {program.faculty}
            </p>
            <h2 className="text-base font-semibold leading-tight truncate">{program.name}</h2>
            {streamLabel && (
              <p className="text-xs text-muted-foreground mt-0.5 truncate">{streamLabel}</p>
            )}
          </div>
        </div>

        {loading && (
          <div className="flex items-center gap-2.5 text-muted-foreground py-12 justify-center text-sm">
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

  // ── Directory ─────────────────────────────────────────────────────────────
  const isSearching = search.trim().length > 0
  const searchResults = isSearching
    ? ALL_PROGRAMS.filter(
        (p) =>
          p.name.toLowerCase().includes(search.toLowerCase()) ||
          p.description.toLowerCase().includes(search.toLowerCase()) ||
          p.faculty.toLowerCase().includes(search.toLowerCase())
      )
    : null

  const displayFaculties = activeFaculty === "All"
    ? FACULTIES
    : FACULTIES.filter((f) => f.name === activeFaculty)

  const totalCount = ALL_PROGRAMS.length

  return (
    <div className="flex flex-col gap-5">
      {/* Header */}
      <div>
        <h2 className="text-lg font-semibold mb-0.5">Programs</h2>
        <p className="text-sm text-muted-foreground">{totalCount} Carleton programs — click any to see requirements</p>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-3.5 text-muted-foreground/40" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search any program…"
          className="w-full pl-9 pr-9 py-2.5 rounded-xl border border-border bg-card text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 placeholder:text-muted-foreground/40"
        />
        {search && (
          <button
            onClick={() => setSearch("")}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground/40 hover:text-muted-foreground transition-colors"
          >
            <X className="size-3.5" />
          </button>
        )}
      </div>

      {/* Faculty tabs — only show when not searching */}
      {!isSearching && (
        <div className="flex gap-1.5 flex-wrap">
          {["All", ...FACULTIES.map((f) => f.name)].map((name) => {
            const faculty = FACULTIES.find((f) => f.name === name)
            const isActive = activeFaculty === name
            return (
              <button
                key={name}
                onClick={() => setActiveFaculty(name)}
                className={cn(
                  "px-3 py-1.5 rounded-lg text-xs font-medium transition-all",
                  isActive
                    ? "bg-foreground text-background"
                    : "border border-border text-muted-foreground hover:text-foreground hover:bg-secondary"
                )}
              >
                {faculty ? faculty.short : "All"}
              </button>
            )
          })}
        </div>
      )}

      {/* Search results */}
      {isSearching ? (
        <div>
          {!searchResults?.length ? (
            <div className="text-center py-12 text-sm text-muted-foreground">No programs found for "{search}"</div>
          ) : (
            <div className="space-y-1.5">
              <p className="text-xs text-muted-foreground mb-3">{searchResults.length} result{searchResults.length !== 1 ? "s" : ""}</p>
              {searchResults.map((p) => {
                const faculty = FACULTIES.find((f) => f.name === p.faculty)!
                return (
                  <ProgramCard
                    key={p.name}
                    program={p}
                    faculty={faculty}
                    onClick={() => handleProgramClick(p)}
                  />
                )
              })}
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-6">
          {displayFaculties.map((faculty) => (
            <div key={faculty.name}>
              <div className="flex items-center gap-2 mb-2.5">
                <span className={cn("size-2 rounded-full", faculty.bgColor)} />
                <h3 className="text-xs font-semibold text-muted-foreground">{faculty.name}</h3>
                <span className="text-xs text-muted-foreground/40">({faculty.programs.length})</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                {faculty.programs.map((p) => (
                  <ProgramCard
                    key={p.name}
                    program={{ ...p, faculty: faculty.name }}
                    faculty={faculty}
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
  faculty,
  onClick,
}: {
  program: Program
  faculty: typeof FACULTIES[number]
  onClick: () => void
}) {
  const hasStreams = !!program.streams?.length
  return (
    <button
      onClick={onClick}
      className="group flex items-center justify-between gap-3 px-4 py-3 rounded-xl border border-border bg-card hover:bg-secondary/30 hover:border-border/60 transition-all text-left"
    >
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-foreground truncate">{program.name}</p>
        <p className="text-xs text-muted-foreground truncate mt-0.5">{program.description}</p>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        {hasStreams && (
          <span className={cn(
            "text-[10px] font-semibold px-1.5 py-0.5 rounded-md",
            faculty.color,
            "bg-current/10"
          )}>
            {program.streams!.length}
          </span>
        )}
        <ChevronRight className="size-3.5 text-muted-foreground/20 group-hover:text-muted-foreground/60 transition-colors" />
      </div>
    </button>
  )
}
