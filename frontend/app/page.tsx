import Link from "next/link"
import { ArrowRight, MessageSquare, BookOpen, BarChart2 } from "lucide-react"

const TOOLS = [
  {
    icon: MessageSquare,
    title: "Chat",
    description: "Ask anything about any course, program, or policy. Get a real answer in seconds, not a link to a PDF.",
  },
  {
    icon: BookOpen,
    title: "Program Explorer",
    description: "Every Carleton program and stream, organized by year. See exactly what you need to graduate.",
  },
  {
    icon: BarChart2,
    title: "Compare Courses",
    description: "Compare up to 3 courses side by side — credits, prerequisites, descriptions. Pick the right one.",
  },
]

const EXAMPLE_QA = [
  {
    q: "What are the prerequisites for SYSC 3110?",
    a: "SYSC 3110 requires SYSC 2100 and SYSC 2004. It's a 0.5 credit course focused on software engineering design.",
  },
  {
    q: "What is the CGPA requirement to stay in Engineering?",
    a: "Engineering students must maintain a CGPA of at least 5.0 (C+) to remain in good standing and continue in their program.",
  },
  {
    q: "What year 2 courses do I need for Computer Systems Engineering?",
    a: "Year 2 includes SYSC 2006, SYSC 2100, SYSC 2310, SYSC 2320, ELEC 2501, ELEC 2607, and ECOR 2050 among others.",
  },
]

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#fafaf9] text-zinc-900 flex flex-col">

      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-zinc-200/60 bg-[#fafaf9]/90 backdrop-blur-xl">
        <div className="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">
          <span className="text-sm font-bold tracking-tight">
            Campus<span className="text-red-600">Q</span>
          </span>
          <div className="flex items-center gap-5">
            <Link href="/about" className="text-sm text-zinc-400 hover:text-zinc-800 transition-colors hidden sm:block">
              About
            </Link>
            <Link
              href="/chat"
              className="inline-flex items-center gap-1.5 bg-zinc-900 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-zinc-800 transition-colors"
            >
              Get started <ArrowRight className="size-3.5" />
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="flex flex-col items-center justify-center text-center px-6 pt-20 pb-16 md:pt-28 md:pb-20">

        <div className="inline-flex items-center gap-2 bg-red-50 border border-red-100 text-red-600 text-xs font-semibold px-3 py-1.5 rounded-full mb-8">
          <span className="relative flex size-1.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-500 opacity-75" />
            <span className="relative inline-flex rounded-full size-1.5 bg-red-500" />
          </span>
          Built for Carleton students, by Carleton students
        </div>

        <h1 className="text-4xl sm:text-5xl md:text-[64px] font-bold tracking-tight leading-[1.06] max-w-3xl text-zinc-900">
          Academic clarity,
          <br />
          <span className="text-red-600">instantly.</span>
        </h1>

        <p className="mt-6 text-base md:text-lg text-zinc-500 max-w-lg leading-relaxed">
          You've got enough to figure out. Your course questions shouldn't be one of them.
        </p>

        <div className="flex flex-col sm:flex-row items-center gap-3 mt-8 w-full sm:w-auto">
          <Link
            href="/chat"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-red-600 hover:bg-red-700 text-white text-sm font-semibold px-7 py-3.5 rounded-xl transition-colors shadow-sm"
          >
            Try it free
            <ArrowRight className="size-4" />
          </Link>
          <Link
            href="/about"
            className="text-sm text-zinc-400 hover:text-zinc-800 transition-colors"
          >
            Learn more →
          </Link>
        </div>

        <p className="mt-6 text-xs text-zinc-400">
          Free account · 3,800+ courses indexed · No advisor queue
        </p>
      </section>

      {/* Example Q&A */}
      <section className="border-t border-zinc-200/60 bg-white py-20 px-6">
        <div className="max-w-3xl mx-auto">
          <p className="text-xs font-semibold text-zinc-400 uppercase tracking-widest text-center mb-10">
            See it in action
          </p>

          {/* Mock app window */}
          <div className="rounded-2xl overflow-hidden border border-zinc-200 shadow-xl shadow-zinc-200/60">

            {/* Window chrome */}
            <div className="bg-zinc-100 border-b border-zinc-200 px-4 py-3 flex items-center gap-2">
              <span className="size-3 rounded-full bg-red-400" />
              <span className="size-3 rounded-full bg-yellow-400" />
              <span className="size-3 rounded-full bg-green-400" />
              <span className="mx-auto text-xs font-medium text-zinc-400">CampusQ</span>
            </div>

            {/* Conversation */}
            <div className="bg-[#fafaf9] p-6 flex flex-col gap-6">
              {EXAMPLE_QA.map((item, i) => (
                <div key={i} className="flex flex-col gap-3">
                  {/* User bubble */}
                  <div className="flex justify-end">
                    <div className="max-w-[75%] bg-zinc-900 text-white text-sm px-4 py-2.5 rounded-2xl rounded-br-sm leading-relaxed">
                      {item.q}
                    </div>
                  </div>
                  {/* Answer */}
                  <div className="flex items-start gap-2.5">
                    <div className="shrink-0 size-6 rounded-md bg-red-600 flex items-center justify-center text-[10px] font-bold text-white mt-0.5">
                      Q
                    </div>
                    <div className="text-sm text-zinc-600 leading-relaxed pt-0.5">{item.a}</div>
                  </div>
                </div>
              ))}
            </div>

            {/* Fake input */}
            <div className="bg-white border-t border-zinc-200 px-4 py-3 flex items-center gap-3">
              <div className="flex-1 bg-zinc-50 border border-zinc-200 rounded-xl px-4 py-2.5 text-xs text-zinc-400">
                Ask anything about Carleton…
              </div>
              <div className="size-8 rounded-xl bg-red-600 flex items-center justify-center shrink-0">
                <ArrowRight className="size-3.5 text-white" />
              </div>
            </div>
          </div>

          <div className="mt-8 text-center">
            <Link
              href="/chat"
              className="inline-flex items-center gap-2 text-sm font-semibold text-red-600 hover:text-red-700 transition-colors"
            >
              Try it yourself <ArrowRight className="size-3.5" />
            </Link>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="border-t border-zinc-200/60 py-16 px-6 bg-[#fafaf9]">
        <div className="max-w-3xl mx-auto">
          <p className="text-xs font-semibold text-zinc-400 uppercase tracking-widest text-center mb-10">
            How it works
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {[
              { step: "01", title: "Ask in plain English", body: "Type your question exactly as you'd ask a friend. No need to know where to look." },
              { step: "02", title: "We search the calendar", body: "CampusQ searches the official Carleton academic calendar in real time." },
              { step: "03", title: "Get an instant answer", body: "Clear, specific, sourced from the actual calendar — not a guess." },
            ].map((s) => (
              <div key={s.step} className="flex flex-col gap-3 p-5 rounded-2xl border border-zinc-200 bg-white">
                <span className="text-xs font-bold text-red-500 tracking-widest">{s.step}</span>
                <p className="text-sm font-semibold text-zinc-900">{s.title}</p>
                <p className="text-xs text-zinc-500 leading-relaxed">{s.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Tools */}
      <section className="border-t border-zinc-200/60 py-16 px-6 bg-white">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-2xl md:text-3xl font-bold text-zinc-900 tracking-tight">
              Three tools, one place.
            </h2>
            <p className="mt-3 text-sm text-zinc-500 max-w-sm mx-auto">
              Built for the questions Carleton students actually have.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {TOOLS.map((f) => {
              const Icon = f.icon
              return (
                <div key={f.title} className="flex flex-col gap-4 p-6 rounded-2xl border border-zinc-200 bg-[#fafaf9]">
                  <div className="size-10 rounded-xl bg-red-50 border border-red-100 flex items-center justify-center">
                    <Icon className="size-4 text-red-600" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-zinc-900">{f.title}</p>
                    <p className="text-xs text-zinc-500 leading-relaxed mt-1.5">{f.description}</p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* Bottom CTA */}
      <section className="border-t border-zinc-200/60 py-20 px-6 relative overflow-hidden bg-zinc-900">
        {/* Subtle red glow */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="size-[600px] rounded-full bg-red-600/10 blur-[120px]" />
        </div>

        <div className="max-w-xl mx-auto text-center relative z-10">
          <div className="inline-flex items-center gap-2 bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-semibold px-3 py-1.5 rounded-full mb-6">
            <span className="relative flex size-1.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
              <span className="relative inline-flex rounded-full size-1.5 bg-red-400" />
            </span>
            Now in beta
          </div>

          <h2 className="text-3xl md:text-5xl font-bold text-white tracking-tight leading-[1.1]">
            Your questions,
            <br />
            <span className="text-red-500">answered now.</span>
          </h2>
          <p className="mt-5 text-zinc-400 text-sm max-w-sm mx-auto leading-relaxed">
            Free account. No advisor queue. Built on the official Carleton academic calendar.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 mt-8">
            <Link
              href="/chat"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-red-600 hover:bg-red-700 text-white text-sm font-semibold px-7 py-3.5 rounded-xl transition-colors"
            >
              Get started free
              <ArrowRight className="size-4" />
            </Link>
            <Link
              href="/about"
              className="text-sm text-zinc-500 hover:text-zinc-300 transition-colors"
            >
              Learn more →
            </Link>
          </div>

          <p className="mt-6 text-xs text-zinc-600">
            Not affiliated with Carleton University
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-zinc-800 px-6 py-6 bg-zinc-900">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
          <span className="text-sm font-bold text-white">
            Campus<span className="text-red-500">Q</span>
          </span>
          <div className="flex items-center gap-5 text-xs text-zinc-500">
            <Link href="/chat" className="hover:text-white transition-colors">App</Link>
            <Link href="/about" className="hover:text-white transition-colors">About</Link>
            <a href="mailto:mahadmyonis@gmail.com" className="hover:text-white transition-colors">Contact</a>
          </div>
        </div>
      </footer>

    </div>
  )
}
