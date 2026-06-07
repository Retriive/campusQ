"use client"

import * as React from "react"
import { Loader2, BookOpen, ArrowLeft, ChevronRight, ChevronDown, GraduationCap, Map } from "lucide-react"
import { DegreePlan } from "./degree-plan"
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
      {
        name: "Architectural Studies",
        description: "Design, urbanism, and conservation — B.A.S.",
        streams: [
          { label: "Design — B.A.S. Honours", queryName: "Design B.A.S. Honours" },
          { label: "Urbanism — B.A.S. Honours", queryName: "Urbanism B.A.S. Honours" },
          { label: "Conservation and Sustainability — B.A.S. Honours", queryName: "Conservation and Sustainability B.A.S. Honours" },
        ],
      },
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
      { name: "Biotechnology", description: "Applied biology, genetic engineering, and bioprocessing" },
      { name: "Geomatics", description: "GIS, remote sensing, and spatial data science" },
      { name: "Integrated Science", description: "Interdisciplinary science across multiple fields" },
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
      { name: "African Studies", description: "History, cultures, and politics of Africa and its diaspora" },
      { name: "Anthropology", description: "Human cultures, evolution, and social organization" },
      { name: "Applied Linguistics and Discourse Studies", description: "Language use, discourse, and teaching English as a second language" },
      { name: "Art History", description: "Visual arts, architecture, and cultural heritage" },
      { name: "Canadian Studies", description: "Canadian history, culture, politics, and society" },
      { name: "Childhood and Youth Studies", description: "Childhood, youth, and the social institutions that shape them" },
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
      { name: "European and Russian Studies", description: "Politics, history, and cultures of Europe and Russia" },
      { name: "Film Studies", description: "Film theory, history, and production" },
      { name: "General Studies", description: "Flexible interdisciplinary B.A. across multiple disciplines" },
      { name: "French", description: "French language, literature, and francophone cultures" },
      { name: "Geography", description: "Physical and human geography, GIS, and spatial analysis" },
      { name: "Global and International Studies", description: "International relations, global politics, and development" },
      { name: "Greek and Roman Studies", description: "Classical civilizations, languages, and archaeology" },
      { name: "History", description: "Historical analysis from ancient to contemporary" },
      { name: "History and Theory of Architecture", description: "Architectural history, theory, and culture" },
      { name: "Humanities", description: "Great books, ideas, and the Western intellectual tradition" },
      { name: "Indigenous Studies", description: "Indigenous histories, cultures, and contemporary issues" },
      { name: "Journalism", description: "News writing, reporting, and digital media" },
      { name: "Journalism and Humanities", description: "Combined journalism with the humanities curriculum" },
      { name: "Latin American and Caribbean Studies", description: "Cultures, politics, and history of Latin America and the Caribbean" },
      { name: "Law and Legal Studies", description: "Legal theory, justice systems, and policy" },
      { name: "Linguistics", description: "Language structure, acquisition, and cognitive linguistics" },
      { name: "Media Production and Design", description: "Multimedia storytelling, production, and design" },
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

// ── Structured requirements types + matching ──────────────────────────────────
interface ReqCourse { code: string; title: string; credits: number | null }
interface ReqGroup { instruction: string; credits: number | null; courses: ReqCourse[] }
interface ProgIndexEntry { slug: string; variants: string[] }

function normalize(s: string): string {
  return s.toLowerCase().replace(/\(.*?\)/g, "").replace(/[^a-z0-9 ]/g, " ").replace(/\s+/g, " ").trim()
}

// Find the (slug, variantKey) whose heading best matches a queryName.
function matchVariant(queryName: string, index: ProgIndexEntry[]): { slug: string; variant: string } | null {
  const nq = normalize(queryName)
  let exact: { slug: string; variant: string } | null = null
  let startsWith: { slug: string; variant: string; len: number } | null = null
  let includes: { slug: string; variant: string; len: number } | null = null
  for (const entry of index) {
    for (const variant of entry.variants) {
      const nv = normalize(variant)
      if (nv === nq) exact = { slug: entry.slug, variant }
      else if (nv.startsWith(nq) && (!startsWith || nv.length < startsWith.len)) startsWith = { slug: entry.slug, variant, len: nv.length }
      else if (nv.includes(nq) && (!includes || nv.length < includes.len)) includes = { slug: entry.slug, variant, len: nv.length }
    }
  }
  if (exact) return exact
  if (startsWith) return { slug: startsWith.slug, variant: startsWith.variant }
  if (includes) return { slug: includes.slug, variant: includes.variant }

  // Fallback: token-overlap (handles inserted words like "Bachelor of Engineering")
  const qTokens = nq.split(" ").filter((t) => t.length > 1)
  let best: { slug: string; variant: string; score: number; len: number } | null = null
  for (const entry of index) {
    for (const variant of entry.variants) {
      const vTokens = new Set(normalize(variant).split(" "))
      const found = qTokens.filter((t) => vTokens.has(t)).length
      const score = qTokens.length ? found / qTokens.length : 0
      const len = normalize(variant).length
      if (score >= 0.8 && (!best || score > best.score || (score === best.score && len < best.len))) {
        best = { slug: entry.slug, variant, score, len }
      }
    }
  }
  return best ? { slug: best.slug, variant: best.variant } : null
}

function totalCredits(variant: string): string | null {
  const m = variant.match(/\((\d+\.?\d*)\s*credits?\)/i)
  return m ? m[1] : null
}

// Classify a stream/option into a type bucket for the grouped picker.

// Turn a raw calendar area header into a friendly section title + color band.
function friendlySection(instruction: string): { title: string; tone: string } {
  const t = instruction.toLowerCase()
  if (/free elective/.test(t)) return { title: "Free Electives", tone: "bg-amber-500" }
  if (/not (included )?in the major|not in communication|in electives not/.test(t)) return { title: "Electives", tone: "bg-blue-500" }
  if (/major cgpa|included in the major|core/.test(t)) return { title: "Major Requirements", tone: "bg-red-500" }
  if (/additional requirement/.test(t)) return { title: "Additional Requirements", tone: "bg-zinc-400" }
  // strip a leading "A. " / "1. " and a trailing credit note
  const cleaned = instruction.replace(/^[A-Z0-9]+\.\s*/, "").replace(/\s*\(\d.*$/, "").trim()
  return { title: cleaned || "Requirements", tone: "bg-zinc-400" }
}

interface Section { title: string; tone: string; credits: number | null; items: ReqGroup[]; courses: ReqCourse[] }

// Group the flat list into A./B./C. sections, nesting numbered sub-requirements.
function buildSections(groups: ReqGroup[]): Section[] {
  const isArea = (g: ReqGroup) => /^[A-Z]\.\s/.test(g.instruction)
  const sections: Section[] = []
  let current: Section | null = null
  for (const g of groups) {
    if (isArea(g)) {
      const f = friendlySection(g.instruction)
      current = { title: f.title, tone: f.tone, credits: g.credits, items: [], courses: g.courses }
      sections.push(current)
    } else {
      if (!current) {
        current = { title: "Requirements", tone: "bg-red-500", credits: null, items: [], courses: [] }
        sections.push(current)
      }
      current.items.push(g)
    }
  }
  return sections
}

function CourseChip({ c }: { c: ReqCourse }) {
  return (
    <span
      title={c.title || undefined}
      className="inline-flex items-center text-[11px] font-mono font-medium px-2 py-1 rounded-md bg-secondary/70 text-foreground/80 hover:bg-secondary transition-colors"
    >
      {c.code}
    </span>
  )
}

function RequirementSection({ section, defaultOpen }: { section: Section; defaultOpen: boolean }) {
  const [open, setOpen] = React.useState(defaultOpen)
  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden">
      <button onClick={() => setOpen(!open)} className="w-full flex items-center gap-3 px-4 py-3 hover:bg-secondary/30 transition-colors text-left">
        <span className={cn("w-1 h-8 rounded-full shrink-0", section.tone)} />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-foreground">{section.title}</p>
        </div>
        {section.credits != null && (
          <span className="text-xs font-mono px-2 py-0.5 rounded-md bg-secondary text-muted-foreground shrink-0">{section.credits} cr</span>
        )}
        <ChevronDown className={cn("size-4 text-muted-foreground/40 transition-transform shrink-0", open && "rotate-180")} />
      </button>

      {open && (
        <div className="px-4 pb-4 pt-1 space-y-3 border-t border-border/40">
          {/* direct courses on the area header (rare) */}
          {section.courses.length > 0 && (
            <div className="flex flex-wrap gap-1.5 pt-3">
              {section.courses.map((c, j) => <CourseChip key={j} c={c} />)}
            </div>
          )}
          {/* numbered sub-requirements */}
          {section.items.map((g, i) => (
            <div key={i} className="pt-3">
              <div className="flex items-start justify-between gap-3 mb-2">
                <p className="text-xs text-muted-foreground leading-snug">
                  {g.instruction.replace(/^\d+\.\s*/, "")}
                </p>
                {g.credits != null && (
                  <span className="shrink-0 text-[10px] font-mono px-1.5 py-0.5 rounded bg-primary/10 text-primary">{g.credits} cr</span>
                )}
              </div>
              {g.courses.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {g.courses.map((c, j) => <CourseChip key={j} c={c} />)}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// Redesigned structured requirements view
function StructuredRequirements({ groups, variant }: { groups: ReqGroup[]; variant: string }) {
  const total = totalCredits(variant)
  const sections = buildSections(groups)
  // credit-breakdown bar from sections that declare credits
  const segs = sections.filter((s) => s.credits != null) as (Section & { credits: number })[]
  const segTotal = segs.reduce((sum, s) => sum + s.credits, 0)

  return (
    <div className="flex flex-col gap-3">
      {/* Header band with total credits + breakdown bar */}
      <div className="rounded-2xl border border-border bg-card p-5">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <GraduationCap className="size-5 text-primary" />
            <span className="text-sm font-medium text-foreground">Degree Requirements</span>
          </div>
          {total && (
            <div className="flex flex-col items-end">
              <span className="text-2xl font-bold text-foreground leading-none tabular-nums">{total}</span>
              <span className="text-[10px] uppercase tracking-wider text-muted-foreground/60">total credits</span>
            </div>
          )}
        </div>

        {segs.length > 1 && segTotal > 0 && (
          <div className="mt-4">
            <div className="flex h-2.5 rounded-full overflow-hidden bg-secondary">
              {segs.map((s, i) => (
                <div key={i} className={cn("h-full", s.tone)} style={{ width: `${(s.credits / segTotal) * 100}%` }} title={`${s.title}: ${s.credits} cr`} />
              ))}
            </div>
            <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2.5">
              {segs.map((s, i) => (
                <span key={i} className="inline-flex items-center gap-1.5 text-[11px] text-muted-foreground">
                  <span className={cn("size-2 rounded-full", s.tone)} /> {s.title} · {s.credits} cr
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Sections */}
      {sections.map((s, i) => (
        <RequirementSection key={i} section={s} defaultOpen={i === 0 || sections.length <= 3} />
      ))}
    </div>
  )
}

// degree abbreviation helpers (adapted from CarletonCourseMap)
function degreeAbbrev(facultyName: string, programName: string): string {
  const p = programName.toLowerCase()
  if (p.includes("computer science") || p.includes("computer mathematics")) return "B.C.S."
  if (p.includes("cybersecurity")) return "B.Cyber."
  if (p.includes("mathematics")) return "B.Math."
  if (p.includes("statistics")) return "B.Math."
  if (p.includes("data science")) return "B.Sc."
  if (p.includes("architecture") && !p.includes("history")) return "B.Arch."
  if (p.includes("journalism")) return "B.J."
  if (p.includes("social work")) return "B.S.W."
  if (p.includes("music")) return "B.Mus."
  if (p.includes("accounting")) return "B.Acc."
  if (p.includes("international business")) return "B.I.B."
  if (p.includes("nursing")) return "B.Sc.N."
  const f = facultyName.toLowerCase()
  if (f.includes("engineering")) return "B.Eng."
  if (f.includes("science")) return "B.Sc."
  if (f.includes("arts")) return "B.A."
  if (f.includes("business")) return "B.Com."
  if (f.includes("public affairs")) return "B.P.A."
  if (f.includes("information technology")) return "B.I.T."
  if (f.includes("health")) return "B.H.Sc."
  return "B.A."
}

type BadgeColors = { bg: string; text: string }
function abbrevColors(ab: string): BadgeColors {
  if (ab.startsWith("B.Eng"))  return { bg: "bg-blue-100 dark:bg-blue-950",   text: "text-blue-700 dark:text-blue-300" }
  if (ab.startsWith("B.Sc"))   return { bg: "bg-emerald-100 dark:bg-emerald-950", text: "text-emerald-700 dark:text-emerald-300" }
  if (ab.startsWith("B.C.S")) return { bg: "bg-red-100 dark:bg-red-950",    text: "text-red-700 dark:text-red-400" }
  if (ab.startsWith("B.Cyber")) return { bg: "bg-red-100 dark:bg-red-950",  text: "text-red-700 dark:text-red-400" }
  if (ab.startsWith("B.A"))    return { bg: "bg-amber-100 dark:bg-amber-950", text: "text-amber-700 dark:text-amber-400" }
  if (ab.startsWith("B.Com")) return { bg: "bg-purple-100 dark:bg-purple-950", text: "text-purple-700 dark:text-purple-400" }
  if (ab.startsWith("B.Math")) return { bg: "bg-indigo-100 dark:bg-indigo-950", text: "text-indigo-700 dark:text-indigo-400" }
  if (ab.startsWith("B.I.T")) return { bg: "bg-cyan-100 dark:bg-cyan-950",  text: "text-cyan-700 dark:text-cyan-400" }
  if (ab.startsWith("B.P.A")) return { bg: "bg-yellow-100 dark:bg-yellow-950", text: "text-yellow-700 dark:text-yellow-500" }
  return                               { bg: "bg-secondary",                  text: "text-muted-foreground" }
}

type ViewState =
  | { screen: "directory" }
  | { screen: "detail"; program: Program; streamLabel?: string; queryName: string }

const ALL_PROGRAMS_SORTED = [...ALL_PROGRAMS].sort((a, b) => a.name.localeCompare(b.name))

export function ProgramExplorer() {
  useCampus()
  const [tab, setTab] = React.useState<"browse" | "plan">("browse")
  const [view, setView] = React.useState<ViewState>({ screen: "directory" })
  const [result, setResult] = React.useState("")
  const [structured, setStructured] = React.useState<{ groups: ReqGroup[]; variant: string } | null>(null)
  const [loading, setLoading] = React.useState(false)
  const [selectedDept, setSelectedDept] = React.useState<Program | null>(null)
  // plan state — tracks chosen slug+variant for DegreePlan
  const [planSlug, setPlanSlug]       = React.useState("")
  const [planVariant, setPlanVariant] = React.useState("")
  const progIndex = React.useRef<ProgIndexEntry[] | null>(null)

  const getIndex = async (): Promise<ProgIndexEntry[]> => {
    if (progIndex.current) return progIndex.current
    let list: ProgIndexEntry[] = []
    try {
      const d = await fetch(`${API_URL}/api/program-requirements`).then((r) => r.json())
      list = d.programs || []
    } catch {
      list = []
    }
    progIndex.current = list
    return list
  }

  // AI fallback — only used when structured data can't be matched
  const loadFromAI = async (queryName: string) => {
    const question = `What are all the required courses for ${queryName} at Carleton University? Please list them organized by year with course codes and credit values. Include any stream-specific requirements.`
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
  }

  const loadRequirements = async (queryName: string) => {
    setResult("")
    setStructured(null)
    setPlanSlug("")
    setPlanVariant("")
    setLoading(true)
    try {
      const index = await getIndex()
      const match = matchVariant(queryName, index)
      if (match) {
        const data = await fetch(`${API_URL}/api/program-requirements?slug=${encodeURIComponent(match.slug)}`).then((r) => r.json())
        const groups: ReqGroup[] = data?.variants?.[match.variant]
        if (groups && groups.length > 0) {
          setStructured({ groups, variant: match.variant })
          setPlanSlug(match.slug)
          setPlanVariant(match.variant)
          setLoading(false)
          return
        }
      }
      await loadFromAI(queryName)
    } catch {
      setResult("Failed to load. Make sure the backend is running.")
    } finally {
      setLoading(false)
    }
  }

  const handleProgramClick = (program: Program) => {
    setView({ screen: "detail", program, queryName: program.name })
    loadRequirements(program.name)
  }

  const handleStreamClick = (program: Program, stream: Stream) => {
    setView({ screen: "detail", program, streamLabel: stream.label, queryName: stream.queryName })
    loadRequirements(stream.queryName)
  }

  const goBack = () => {
    setView({ screen: "directory" })
    setResult("")
    setStructured(null)
  }

  // ── Detail view ───────────────────────────────────────────────────────────
  if (view.screen === "detail") {
    const { program, streamLabel } = view as { program: Program; streamLabel?: string; queryName: string }
    const faculty = FACULTIES.find((f) => f.name === program.faculty)
    const hasPlan = !!planSlug && !!planVariant

    return (
      <div className="flex flex-col gap-4">
        {/* Back + title */}
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

        {/* Sub-tabs: Requirements | My Plan */}
        <div className="flex gap-1 p-1 rounded-xl bg-secondary/50 w-fit">
          <button
            onClick={() => setTab("browse")}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all",
              tab === "browse" ? "bg-background shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground"
            )}
          >
            <BookOpen className="size-3.5" /> Requirements
          </button>
          <button
            onClick={() => setTab("plan")}
            disabled={!hasPlan && !loading}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all",
              tab === "plan" ? "bg-background shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground",
              !hasPlan && !loading && "opacity-40 cursor-not-allowed"
            )}
          >
            <Map className="size-3.5" /> My Plan
          </button>
        </div>

        {/* Requirements tab */}
        {tab === "browse" && (
          <>
            {loading && (
              <div className="flex items-center gap-2.5 text-muted-foreground py-12 justify-center text-sm">
                <Loader2 className="size-4 animate-spin" />
                Loading requirements…
              </div>
            )}
            {structured && <StructuredRequirements groups={structured.groups} variant={structured.variant} />}
            {result && !structured && (
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
          </>
        )}

        {/* My Plan tab */}
        {tab === "plan" && hasPlan && (
          <DegreePlan slug={planSlug} variant={planVariant} />
        )}
        {tab === "plan" && !hasPlan && loading && (
          <div className="flex items-center gap-2.5 text-muted-foreground py-12 justify-center text-sm">
            <Loader2 className="size-4 animate-spin" /> Loading…
          </div>
        )}
      </div>
    )
  }

  // ── Directory ─────────────────────────────────────────────────────────────
  const deptFaculty = selectedDept
    ? FACULTIES.find((f) => f.name === selectedDept.faculty)!
    : null

  const handleDeptChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const name = e.target.value
    if (!name) { setSelectedDept(null); return }
    const prog = ALL_PROGRAMS_SORTED.find((p) => p.name === name)
    if (!prog) return
    setSelectedDept(prog)
  }

  return (
    <div className="flex flex-col gap-5">
      {/* Header */}
      <div>
        <h2 className="text-lg font-semibold mb-0.5">Programs</h2>
        <p className="text-sm text-muted-foreground">{ALL_PROGRAMS.length} Carleton programs</p>
      </div>

      {/* Department dropdown */}
      <div className="flex flex-col gap-1.5">
        <label className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">
          Department
        </label>
        <div className="relative">
          <select
            value={selectedDept?.name ?? ""}
            onChange={handleDeptChange}
            className="w-full appearance-none rounded-xl border border-border bg-card px-4 py-2.5 pr-9 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 cursor-pointer"
          >
            <option value="">Select department…</option>
            {ALL_PROGRAMS_SORTED.map((p) => (
              <option key={p.name} value={p.name}>{p.name}</option>
            ))}
          </select>
          <ChevronDown className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 size-3.5 text-muted-foreground/50" />
        </div>
      </div>

      {/* Program cards for selected department */}
      {selectedDept && (
        <div className="flex flex-col gap-3">
          {deptFaculty && (
            <p className={cn("text-[10px] font-semibold uppercase tracking-widest", deptFaculty.color)}>
              {deptFaculty.name}
            </p>
          )}
          {selectedDept.streams && selectedDept.streams.length > 0 ? (
            <div className="grid grid-cols-2 gap-2">
              {selectedDept.streams.map((stream) => {
                const ab = degreeAbbrev(selectedDept.faculty, stream.label)
                const colors = abbrevColors(ab)
                return (
                  <button
                    key={stream.queryName}
                    onClick={() => handleStreamClick(selectedDept, stream)}
                    className="group flex flex-col items-start gap-2 rounded-xl border border-border bg-card hover:border-primary/40 hover:bg-secondary/30 hover:-translate-y-px transition-all text-left p-3"
                  >
                    <span className={cn("inline-block text-[10px] font-bold font-mono px-2 py-0.5 rounded tracking-wide", colors.bg, colors.text)}>
                      {ab}
                    </span>
                    <span className="text-xs font-medium text-foreground leading-snug line-clamp-2">{stream.label}</span>
                  </button>
                )
              })}
            </div>
          ) : (
            <button
              onClick={() => handleProgramClick(selectedDept)}
              className="group flex flex-col items-start gap-2 rounded-xl border border-border bg-card hover:border-primary/40 hover:bg-secondary/30 hover:-translate-y-px transition-all text-left p-3 w-full"
            >
              {(() => {
                const ab = degreeAbbrev(selectedDept.faculty, selectedDept.name)
                const colors = abbrevColors(ab)
                return (
                  <>
                    <span className={cn("inline-block text-[10px] font-bold font-mono px-2 py-0.5 rounded tracking-wide", colors.bg, colors.text)}>
                      {ab}
                    </span>
                    <span className="text-sm font-medium text-foreground">{selectedDept.name}</span>
                  </>
                )
              })()}
            </button>
          )}
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
  const ab = degreeAbbrev(faculty.name, program.name)
  const colors = abbrevColors(ab)
  const count = program.streams?.length ?? 0
  return (
    <button
      onClick={onClick}
      className="group flex flex-col items-start gap-2 rounded-xl border border-border bg-card hover:border-primary/40 hover:bg-secondary/30 hover:-translate-y-px transition-all text-left p-3"
    >
      {/* Degree badge */}
      <span className={cn("inline-block text-[10px] font-bold font-mono px-2 py-0.5 rounded tracking-wide", colors.bg, colors.text)}>
        {ab}
      </span>

      {/* Program name */}
      <span className="text-xs font-medium text-foreground leading-snug line-clamp-2">{program.name}</span>

      {/* Options count */}
      {count > 0 && (
        <span className="text-[10px] text-muted-foreground/60 mt-auto">
          {count} options
        </span>
      )}
    </button>
  )
}
