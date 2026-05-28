import Link from "next/link"
import { ArrowRight, GitBranch, GraduationCap, BarChart2, MessageSquare } from "lucide-react"

const FEATURES = [
  {
    icon: MessageSquare,
    title: "Course lookup",
    description: "Ask anything about any Carleton course in plain English.",
  },
  {
    icon: GitBranch,
    title: "Prerequisite tree",
    description: "See the full dependency chain for any course, visually.",
  },
  {
    icon: GraduationCap,
    title: "Degree planner",
    description: "Map out your 4-year schedule with drag-and-drop.",
  },
  {
    icon: BarChart2,
    title: "Course comparison",
    description: "Compare up to 3 courses side by side.",
  },
]

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white text-zinc-900 flex flex-col">

      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-zinc-100 bg-white/90 backdrop-blur-xl">
        <div className="max-w-4xl mx-auto px-6 h-14 flex items-center justify-between">
          <span className="text-sm font-semibold tracking-tight">
            Campus<span className="text-red-600">Q</span>
          </span>
          <div className="flex items-center gap-6">
            <Link href="/about" className="text-sm text-zinc-400 hover:text-zinc-900 transition-colors">
              About
            </Link>
            <Link
              href="/chat"
              className="inline-flex items-center gap-1.5 bg-zinc-900 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-zinc-700 transition-colors"
            >
              Open app <ArrowRight className="size-3.5" />
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="flex-1 flex flex-col items-center justify-center text-center px-6 py-32">
        <p className="text-xs font-medium text-red-600 uppercase tracking-widest mb-5">
          Made by a Carleton student
        </p>
        <h1 className="text-5xl md:text-6xl font-bold tracking-tight leading-[1.08] max-w-2xl text-zinc-900">
          Stop digging through the Carleton calendar.
        </h1>
        <p className="mt-6 text-lg text-zinc-500 max-w-md leading-relaxed">
          Instant answers about courses, prerequisites, and programs — sourced from the official academic calendar.
        </p>
        <div className="flex items-center gap-3 mt-10">
          <Link
            href="/chat"
            className="inline-flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white text-sm font-semibold px-6 py-3 rounded-xl transition-colors"
          >
            Try it free
            <ArrowRight className="size-4" />
          </Link>
          <Link
            href="/about"
            className="text-sm text-zinc-500 hover:text-zinc-900 transition-colors"
          >
            Learn more →
          </Link>
        </div>
        <p className="mt-8 text-xs text-zinc-400">
          Free · No account required · 7,700+ courses indexed
        </p>
      </section>

      {/* Features */}
      <section className="border-t border-zinc-100 bg-zinc-50/50 py-20 px-6">
        <div className="max-w-4xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {FEATURES.map((f) => {
              const Icon = f.icon
              return (
                <div key={f.title} className="flex flex-col gap-3">
                  <div className="flex items-center justify-center size-9 rounded-lg bg-red-50 border border-red-100">
                    <Icon className="size-4 text-red-600" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-zinc-900">{f.title}</p>
                    <p className="text-xs text-zinc-500 leading-relaxed mt-1">{f.description}</p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-zinc-100 px-6 py-6">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <span className="text-sm font-semibold">
            Campus<span className="text-red-600">Q</span>
          </span>
          <div className="flex items-center gap-5 text-xs text-zinc-400">
            <Link href="/about" className="hover:text-zinc-900 transition-colors">About</Link>
            <Link href="/chat" className="hover:text-zinc-900 transition-colors">App</Link>
            <span>Not affiliated with Carleton University</span>
          </div>
        </div>
      </footer>

    </div>
  )
}
