import Link from "next/link"
import { ArrowRight, Calculator, CalendarDays, BarChart2, BookOpen } from "lucide-react"

const DEMO_MESSAGES = [
  {
    role: "user",
    text: "Can I take COMP 2401 without finishing COMP 1405?",
  },
  {
    role: "assistant",
    text: "No — COMP 2401 requires either COMP 1405 or COMP 1406 as a prerequisite. You'll need to complete one of those first before registering.",
  },
  {
    role: "user",
    text: "What's the last day to drop a course this fall?",
  },
  {
    role: "assistant",
    text: "For Fall 2026, the last day to withdraw from a full fall course without academic notation is November 15th.",
  },
]

const STATS = [
  { value: "3,782", label: "courses indexed" },
  { value: "84",    label: "programs covered" },
  { value: "498",   label: "degree variants" },
  { value: "0",     label: "advisor queues" },
]

const TOOLS = [
  {
    icon: BookOpen,
    name: "Program Explorer",
    desc: "Every Carleton program, stream, and concentration — with requirements listed by year.",
  },
  {
    icon: Calculator,
    name: "GPA Calculator",
    desc: "Carleton's 12-point scale. Add courses, see your CGPA. Run what-if scenarios for next semester.",
  },
  {
    icon: CalendarDays,
    name: "Deadline Tracker",
    desc: "Add/drop dates, exam periods, payment deadlines — with live countdowns so nothing sneaks up on you.",
  },
  {
    icon: BarChart2,
    name: "Course Compare",
    desc: "Put up to 3 courses side by side. Credits, prerequisites, descriptions. Pick the right one.",
  },
]

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white text-zinc-900 flex flex-col selection:bg-red-100">

      {/* Nav */}
      <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-xl border-b border-zinc-100">
        <div className="max-w-6xl mx-auto px-5 h-14 flex items-center justify-between">
          <span className="text-sm font-bold tracking-tight">
            Campus<span className="text-red-600">Q</span>
          </span>
          <div className="flex items-center gap-4">
            <Link href="/about" className="text-sm text-zinc-400 hover:text-zinc-800 transition-colors hidden sm:block">
              About
            </Link>
            <Link
              href="/chat"
              className="inline-flex items-center gap-1.5 bg-zinc-900 hover:bg-zinc-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
            >
              Open app <ArrowRight className="size-3.5" />
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-6xl mx-auto px-5 pt-16 pb-12 md:pt-24 md:pb-16 w-full">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center">

          {/* Left */}
          <div>
            <div className="inline-flex items-center gap-2 text-xs font-semibold text-red-600 bg-red-50 px-3 py-1.5 rounded-full mb-6">
              <span className="relative flex size-1.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-500 opacity-60" />
                <span className="relative inline-flex rounded-full size-1.5 bg-red-500" />
              </span>
              Built for Carleton students
            </div>

            <h1 className="text-[42px] sm:text-5xl lg:text-[56px] font-bold tracking-tight leading-[1.06] text-zinc-900">
              Academic clarity,
              <br />
              <span className="text-red-600">instantly.</span>
            </h1>

            <p className="mt-5 text-zinc-500 text-base leading-relaxed max-w-sm">
              You've got enough to figure out. Your course questions shouldn't be one of them.
            </p>

            <div className="flex items-center gap-3 mt-8">
              <Link
                href="/chat"
                className="inline-flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white text-sm font-semibold px-6 py-3 rounded-xl transition-colors shadow-sm shadow-red-200"
              >
                Try it free
                <ArrowRight className="size-4" />
              </Link>
              <Link href="/about" className="text-sm text-zinc-400 hover:text-zinc-700 transition-colors">
                Learn more →
              </Link>
            </div>

            <p className="mt-5 text-xs text-zinc-400">
              Free to sign up · Built on official Carleton documents
            </p>
          </div>

          {/* Right — chat mockup */}
          <div className="relative">
            {/* Subtle background glow */}
            <div className="absolute -inset-4 bg-gradient-to-br from-red-50 to-zinc-50 rounded-3xl -z-10" />

            <div className="rounded-2xl border border-zinc-200 overflow-hidden shadow-2xl shadow-zinc-200/80">
              {/* Window bar */}
              <div className="bg-zinc-50 border-b border-zinc-200 px-4 py-3 flex items-center gap-2">
                <span className="size-2.5 rounded-full bg-red-400" />
                <span className="size-2.5 rounded-full bg-yellow-400" />
                <span className="size-2.5 rounded-full bg-green-400" />
                <span className="ml-auto text-[11px] text-zinc-400 font-medium">CampusQ</span>
              </div>

              {/* Messages */}
              <div className="bg-white px-5 py-5 flex flex-col gap-4">
                {DEMO_MESSAGES.map((msg, i) => (
                  <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start gap-2.5"}`}>
                    {msg.role === "assistant" && (
                      <div className="shrink-0 size-6 rounded-md bg-red-600 flex items-center justify-center text-[10px] font-bold text-white mt-0.5">
                        Q
                      </div>
                    )}
                    <div className={`max-w-[82%] text-sm leading-relaxed rounded-2xl px-3.5 py-2.5 ${
                      msg.role === "user"
                        ? "bg-zinc-900 text-white rounded-br-sm"
                        : "bg-zinc-50 text-zinc-700 rounded-bl-sm border border-zinc-100"
                    }`}>
                      {msg.text}
                    </div>
                  </div>
                ))}
              </div>

              {/* Fake input */}
              <div className="bg-white border-t border-zinc-100 px-4 py-3 flex items-center gap-2.5">
                <div className="flex-1 bg-zinc-50 border border-zinc-200 rounded-xl px-3.5 py-2 text-xs text-zinc-400">
                  Ask anything about Carleton…
                </div>
                <button className="size-8 bg-red-600 rounded-xl flex items-center justify-center shrink-0">
                  <ArrowRight className="size-3.5 text-white" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats strip */}
      <div className="border-y border-zinc-100 bg-zinc-50">
        <div className="max-w-6xl mx-auto px-5 py-6">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-6">
            {STATS.map((s) => (
              <div key={s.label} className="flex flex-col items-center sm:items-start gap-0.5">
                <span className="text-2xl font-bold text-zinc-900 tabular-nums">{s.value}</span>
                <span className="text-xs text-zinc-500">{s.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Tools */}
      <section className="max-w-6xl mx-auto px-5 py-16 md:py-24 w-full">
        <div className="mb-10">
          <p className="text-xs font-semibold uppercase tracking-widest text-zinc-400 mb-3">What's inside</p>
          <h2 className="text-2xl md:text-3xl font-bold text-zinc-900 tracking-tight max-w-sm leading-snug">
            More than just a chatbot.
          </h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {TOOLS.map((t) => {
            const Icon = t.icon
            return (
              <div
                key={t.name}
                className="flex gap-4 p-5 rounded-2xl border border-zinc-100 bg-zinc-50 hover:border-zinc-200 hover:bg-white transition-all"
              >
                <div className="shrink-0 size-9 rounded-xl bg-white border border-zinc-200 shadow-sm flex items-center justify-center">
                  <Icon className="size-4 text-zinc-700" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-zinc-900 mb-1">{t.name}</p>
                  <p className="text-xs text-zinc-500 leading-relaxed">{t.desc}</p>
                </div>
              </div>
            )
          })}
        </div>
      </section>

      {/* CTA */}
      <section className="bg-zinc-900 relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute -top-32 -right-32 size-96 rounded-full bg-red-600/10 blur-[100px]" />
          <div className="absolute -bottom-32 -left-32 size-96 rounded-full bg-red-600/5 blur-[100px]" />
        </div>

        <div className="max-w-6xl mx-auto px-5 py-20 md:py-28 relative z-10">
          <div className="max-w-xl">
            <p className="text-xs font-semibold uppercase tracking-widest text-zinc-500 mb-5">Get started</p>
            <h2 className="text-3xl md:text-5xl font-bold text-white tracking-tight leading-[1.1]">
              Your questions,
              <br />
              <span className="text-red-500">answered now.</span>
            </h2>
            <p className="mt-5 text-zinc-400 text-sm leading-relaxed max-w-sm">
              Free. No advisor queue. No calendar rabbit holes. Just ask.
            </p>

            <div className="flex items-center gap-3 mt-8">
              <Link
                href="/chat"
                className="inline-flex items-center gap-2 bg-red-600 hover:bg-red-500 text-white text-sm font-semibold px-6 py-3 rounded-xl transition-colors"
              >
                Open CampusQ free
                <ArrowRight className="size-4" />
              </Link>
            </div>

            <p className="mt-5 text-xs text-zinc-600">
              Not affiliated with Carleton University
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-zinc-900 border-t border-zinc-800 px-5 py-6">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
          <span className="text-sm font-bold text-zinc-400">
            Campus<span className="text-red-500">Q</span>
          </span>
          <div className="flex items-center gap-5 text-xs text-zinc-600">
            <Link href="/chat" className="hover:text-white transition-colors">App</Link>
            <Link href="/about" className="hover:text-white transition-colors">About</Link>
            <a href="mailto:mahadmyonis@gmail.com" className="hover:text-white transition-colors">Contact</a>
          </div>
        </div>
      </footer>

    </div>
  )
}
