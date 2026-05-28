import Link from "next/link"
import { ArrowRight, GitBranch, GraduationCap, BarChart2, MessageSquare, Zap, Shield, BookOpen } from "lucide-react"

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white flex flex-col overflow-x-hidden">

      {/* ── Nav ── */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-white/[0.06] bg-[#0a0a0a]/80 backdrop-blur-xl">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <span className="text-sm font-semibold tracking-tight">
            Campus<span className="text-red-500">Q</span>
          </span>
          <div className="flex items-center gap-8">
            <div className="hidden md:flex items-center gap-7">
              <Link href="#features" className="text-xs text-white/50 hover:text-white/90 transition-colors">Features</Link>
              <Link href="/about" className="text-xs text-white/50 hover:text-white/90 transition-colors">About</Link>
            </div>
            <Link
              href="/chat"
              className="inline-flex items-center gap-1.5 bg-white text-black text-xs font-semibold px-4 py-2 rounded-lg hover:bg-white/90 transition-colors"
            >
              Open app <ArrowRight className="size-3" />
            </Link>
          </div>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="relative flex flex-col items-center justify-center text-center px-6 pt-40 pb-28">
        {/* Background glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-red-600/10 blur-[120px] rounded-full pointer-events-none" />
        <div className="absolute top-20 left-1/2 -translate-x-1/2 w-[400px] h-[200px] bg-red-500/8 blur-[80px] rounded-full pointer-events-none" />

        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-white/10 bg-white/[0.04] text-xs text-white/50 mb-8">
          <span className="relative flex size-1.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
            <span className="relative inline-flex rounded-full size-1.5 bg-green-400" />
          </span>
          Made by a Carleton student who got tired of the PDF
        </div>

        {/* Headline */}
        <h1 className="text-5xl md:text-7xl font-bold tracking-tight leading-[1.05] max-w-4xl">
          Stop digging through
          <br />
          the{" "}
          <span
            style={{
              background: "linear-gradient(135deg, #ef4444 0%, #dc2626 50%, #b91c1c 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
            }}
          >
            Carleton calendar.
          </span>
        </h1>

        <p className="mt-6 text-base md:text-lg text-white/50 max-w-lg leading-relaxed">
          As a Carleton student I wasted hours every semester hunting prerequisites, decoding program requirements, and waiting on advisors. I built CampusQ so you don't have to.
        </p>

        {/* CTAs */}
        <div className="flex flex-col sm:flex-row items-center gap-3 mt-10">
          <Link
            href="/chat"
            className="inline-flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white text-sm font-semibold px-6 py-3 rounded-xl transition-colors shadow-lg shadow-red-900/30"
          >
            Try CampusQ free
            <ArrowRight className="size-4" />
          </Link>
          <Link
            href="#features"
            className="inline-flex items-center gap-2 border border-white/10 bg-white/[0.04] hover:bg-white/[0.08] text-white/70 hover:text-white text-sm font-medium px-6 py-3 rounded-xl transition-all"
          >
            See what it can do
          </Link>
        </div>

        {/* Social proof */}
        <p className="mt-10 text-xs text-white/30">
          Free to use · No account required · Not affiliated with Carleton University
        </p>
      </section>

      {/* ── Product mockup ── */}
      <section className="px-6 pb-24 max-w-5xl mx-auto w-full">
        <div className="relative rounded-2xl border border-white/[0.08] bg-[#111111] overflow-hidden shadow-2xl shadow-black/60">
          {/* Fake browser bar */}
          <div className="flex items-center gap-2 px-4 py-3 border-b border-white/[0.06] bg-[#0d0d0d]">
            <div className="flex items-center gap-1.5">
              <div className="size-3 rounded-full bg-white/10" />
              <div className="size-3 rounded-full bg-white/10" />
              <div className="size-3 rounded-full bg-white/10" />
            </div>
            <div className="flex-1 mx-4">
              <div className="h-6 rounded-md bg-white/[0.05] max-w-xs mx-auto flex items-center justify-center">
                <span className="text-[10px] text-white/20 font-mono">campusq.app/chat</span>
              </div>
            </div>
          </div>

          {/* Mock chat UI */}
          <div className="p-6 md:p-10 flex flex-col gap-5 min-h-[340px]">
            {/* User message */}
            <div className="flex justify-end">
              <div className="bg-red-600 text-white text-sm px-4 py-3 rounded-2xl rounded-tr-sm max-w-xs shadow-lg">
                What are the prerequisites for SYSC 3110?
              </div>
            </div>

            {/* AI response */}
            <div className="flex gap-3 max-w-xl">
              <div className="shrink-0 size-7 rounded-lg bg-red-600 flex items-center justify-center mt-0.5">
                <span className="text-white text-[10px] font-bold">Q</span>
              </div>
              <div className="bg-white/[0.05] border border-white/[0.08] text-white/80 text-sm px-4 py-3.5 rounded-2xl rounded-tl-sm leading-relaxed">
                <p className="text-white font-medium mb-2">SYSC 3110 — Software Engineering Design</p>
                <p className="text-white/60 text-xs mb-3">0.5 credits</p>
                <p className="text-white/70 mb-4">An introduction to the design and implementation of large-scale software systems using object-oriented design techniques.</p>
                <div>
                  <p className="text-xs font-semibold text-white/40 uppercase tracking-wider mb-2">Prerequisites</p>
                  <div className="flex flex-wrap gap-1.5">
                    {["SYSC 2100", "SYSC 2004"].map((p) => (
                      <span key={p} className="px-2.5 py-1 rounded-md bg-white/[0.07] border border-white/10 text-xs font-mono text-white/60">
                        {p}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Typing indicator */}
            <div className="flex gap-3 items-center">
              <div className="shrink-0 size-7 rounded-lg bg-red-600 flex items-center justify-center">
                <span className="text-white text-[10px] font-bold">Q</span>
              </div>
              <div className="bg-white/[0.05] border border-white/[0.08] px-4 py-3 rounded-2xl rounded-tl-sm">
                <div className="flex gap-1 items-center">
                  <span className="size-1.5 rounded-full bg-white/30 animate-bounce [animation-delay:-0.3s]" />
                  <span className="size-1.5 rounded-full bg-white/30 animate-bounce [animation-delay:-0.15s]" />
                  <span className="size-1.5 rounded-full bg-white/30 animate-bounce" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Stats bar ── */}
      <section className="border-y border-white/[0.06] bg-white/[0.02] py-10 px-6">
        <div className="max-w-4xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
          {[
            { value: "3,600+", label: "Courses indexed" },
            { value: "4,100+", label: "Programs & docs" },
            { value: "<1s", label: "Average response" },
            { value: "Free", label: "Always" },
          ].map((s) => (
            <div key={s.label}>
              <p className="text-2xl md:text-3xl font-bold text-white">{s.value}</p>
              <p className="text-xs text-white/40 mt-1">{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Features ── */}
      <section id="features" className="max-w-6xl mx-auto px-6 py-28 w-full">
        <div className="text-center mb-16">
          <p className="text-xs font-semibold text-red-500 uppercase tracking-widest mb-3">Features</p>
          <h2 className="text-3xl md:text-5xl font-bold tracking-tight">
            Built for how students actually think
          </h2>
          <p className="mt-4 text-white/50 max-w-xl mx-auto text-base">
            Not a search bar. Not a chatbot. A proper academic tool that understands your questions.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            {
              icon: MessageSquare,
              title: "Natural language course lookup",
              description:
                "Ask \"what do I need before taking SYSC 4906?\" and get a real answer — not a list of links. CampusQ reads the calendar so you don't have to.",
              tag: "Core",
            },
            {
              icon: GitBranch,
              title: "Prerequisite chain visualizer",
              description:
                "See the full dependency tree for any course. Know exactly what you need to take — and in what order — before you can enroll in a course.",
              tag: "Visual",
            },
            {
              icon: GraduationCap,
              title: "4-year degree planner",
              description:
                "Drag and drop courses across 8 semesters. Build your entire degree plan and save it — no sign-up required.",
              tag: "Planner",
            },
            {
              icon: BarChart2,
              title: "Side-by-side course comparison",
              description:
                "Can't decide between two electives? Compare up to 3 courses side by side — credits, prerequisites, and full descriptions.",
              tag: "Tools",
            },
          ].map((f) => {
            const Icon = f.icon
            return (
              <div
                key={f.title}
                className="group flex flex-col gap-5 p-7 rounded-2xl border border-white/[0.07] bg-white/[0.02] hover:bg-white/[0.04] hover:border-white/[0.12] transition-all duration-200"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center justify-center size-10 rounded-xl bg-red-600/15 border border-red-500/20">
                    <Icon className="size-5 text-red-400" />
                  </div>
                  <span className="text-[10px] font-semibold text-white/25 uppercase tracking-widest border border-white/[0.07] px-2.5 py-1 rounded-full">
                    {f.tag}
                  </span>
                </div>
                <div>
                  <h3 className="text-base font-semibold text-white">{f.title}</h3>
                  <p className="text-sm text-white/45 leading-relaxed mt-2">{f.description}</p>
                </div>
              </div>
            )
          })}
        </div>
      </section>

      {/* ── Trust bar ── */}
      <section className="border-t border-white/[0.06] py-12 px-6">
        <div className="max-w-4xl mx-auto flex flex-wrap justify-center gap-8">
          {[
            { icon: Shield, label: "Not affiliated with Carleton University" },
            { icon: Zap, label: "Powered by OpenAI + Pinecone" },
            { icon: BookOpen, label: "Official calendar as source of truth" },
          ].map((t) => {
            const Icon = t.icon
            return (
              <div key={t.label} className="flex items-center gap-2.5 text-xs text-white/30">
                <Icon className="size-3.5" />
                {t.label}
              </div>
            )
          })}
        </div>
      </section>

      {/* ── Final CTA ── */}
      <section className="border-t border-white/[0.06] py-32 px-6 text-center">
        <div className="max-w-2xl mx-auto">
          <h2 className="text-4xl md:text-6xl font-bold tracking-tight leading-tight">
            Your degree is too
            <br />
            important to guess.
          </h2>
          <p className="mt-5 text-white/45 text-base max-w-md mx-auto">
            Get clear answers from the actual Carleton calendar — not Reddit threads, not outdated advice, not a 3-week wait for an advisor appointment.
          </p>
          <Link
            href="/chat"
            className="inline-flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white text-sm font-semibold px-8 py-4 rounded-xl transition-colors mt-10 shadow-xl shadow-red-900/30"
          >
            Try it free — no account needed
            <ArrowRight className="size-4" />
          </Link>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-white/[0.06] px-6 py-8">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <span className="text-sm font-semibold">
            Campus<span className="text-red-500">Q</span>
          </span>
          <div className="flex items-center gap-6 text-xs text-white/30">
            <Link href="/chat" className="hover:text-white/70 transition-colors">App</Link>
            <Link href="/about" className="hover:text-white/70 transition-colors">About</Link>
            <span>© 2025 CampusQ. Independent, not affiliated with Carleton University.</span>
          </div>
        </div>
      </footer>

    </div>
  )
}
