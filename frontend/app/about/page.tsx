import { Metadata } from "next"
import Link from "next/link"
import { ArrowRight, ShieldCheck, Mail } from "lucide-react"

export const metadata: Metadata = {
  title: "About — CampusQ",
  description: "CampusQ is an independent AI academic assistant for Carleton University students.",
}

const CAPABILITIES = [
  "Look up any course — description, prerequisites, and credit value",
  "Answer questions about program requirements for any Carleton program",
  "Show the full prerequisite chain for any course, visually",
  "Help you plan your degree semester by semester",
  "Tell you which courses you're now eligible for based on what you've completed",
  "Compare courses side by side to help you choose",
  "Explain university policies in plain language",
]

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white flex flex-col">

      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-white/[0.06] bg-[#0a0a0a]/80 backdrop-blur-xl">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <Link href="/" className="text-sm font-semibold tracking-tight">
            Campus<span className="text-red-500">Q</span>
          </Link>
          <Link
            href="/chat"
            className="inline-flex items-center gap-1.5 bg-white text-black text-xs font-semibold px-4 py-2 rounded-lg hover:bg-white/90 transition-colors"
          >
            Open app <ArrowRight className="size-3" />
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative px-6 pt-24 pb-16 text-center">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-red-600/8 blur-[100px] rounded-full pointer-events-none" />
        <div className="max-w-2xl mx-auto relative">
          <p className="text-xs font-semibold text-red-500 uppercase tracking-widest mb-4">About</p>
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight leading-tight">
            I was a Carleton student.
            <br />
            <span className="text-white/30">This is what I needed.</span>
          </h1>
          <p className="mt-6 text-white/50 text-base leading-relaxed max-w-lg mx-auto">
            Hours wasted in the calendar. Advisors booked out for weeks. Questions that should take seconds taking days. I built CampusQ to fix that.
          </p>
        </div>
      </section>

      {/* Main content */}
      <main className="max-w-2xl mx-auto px-6 py-16 w-full flex flex-col gap-16">

        {/* Origin story */}
        <section className="flex flex-col gap-4">
          <h2 className="text-xl font-semibold text-white">Why I built this</h2>
          <p className="text-white/50 leading-relaxed text-sm">
            Every semester at Carleton, the same thing — open five PDFs, cross-reference prerequisites,
            try to figure out if you actually qualify for a course, wait two weeks for an advisor to
            confirm what you could've found out in 30 seconds. The information existed. It was just
            completely inaccessible.
          </p>
          <p className="text-white/50 leading-relaxed text-sm">
            So I indexed the entire Carleton academic calendar — every course, every program, every
            policy — and built an AI that can answer your questions from it directly. No fluff,
            no guessing, no Reddit threads from 2019.
          </p>
          <p className="text-white/50 leading-relaxed text-sm">
            CampusQ is what I built because I got fed up. And it's free because every student
            deserves access to clear information about their own degree.
          </p>
        </section>

        {/* Capabilities */}
        <section className="flex flex-col gap-5">
          <h2 className="text-xl font-semibold text-white">What it can do</h2>
          <div className="flex flex-col gap-3">
            {CAPABILITIES.map((item) => (
              <div key={item} className="flex items-start gap-3 p-4 rounded-xl border border-white/[0.07] bg-white/[0.02]">
                <span className="size-1.5 rounded-full bg-red-500 mt-2 shrink-0" />
                <span className="text-sm text-white/60 leading-relaxed">{item}</span>
              </div>
            ))}
          </div>
        </section>

        {/* Disclaimer */}
        <section className="rounded-xl border border-white/10 bg-white/[0.03] p-6 flex flex-col gap-3">
          <div className="flex items-center gap-2.5">
            <ShieldCheck className="size-4 text-red-400 shrink-0" />
            <span className="text-sm font-semibold text-white">Important disclaimer</span>
          </div>
          <p className="text-sm text-white/45 leading-relaxed">
            CampusQ is an <span className="text-white/70 font-medium">independent student tool</span> and
            is <span className="text-white/70 font-medium">not affiliated with, endorsed by, or operated
            by Carleton University</span>. While we strive for accuracy, always verify important academic
            decisions with your advisor or the official calendar at{" "}
            <a
              href="https://calendar.carleton.ca"
              target="_blank"
              rel="noopener noreferrer"
              className="text-red-400 hover:text-red-300 transition-colors underline underline-offset-2"
            >
              calendar.carleton.ca
            </a>.
          </p>
        </section>

        {/* Contact */}
        <section className="flex flex-col gap-4">
          <h2 className="text-xl font-semibold text-white">Contact</h2>
          <p className="text-sm text-white/45">
            Found an error, have feedback, or want to get in touch? Use the feedback button inside the
            app, or reach out directly:
          </p>
          <a
            href="mailto:campusq@proton.me"
            className="inline-flex items-center gap-2 text-sm text-red-400 hover:text-red-300 transition-colors"
          >
            <Mail className="size-4" />
            campusq@proton.me
          </a>
        </section>

      </main>

      {/* Footer */}
      <footer className="border-t border-white/[0.06] px-6 py-8 mt-auto">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <Link href="/" className="text-sm font-semibold">
            Campus<span className="text-red-500">Q</span>
          </Link>
          <div className="flex items-center gap-6 text-xs text-white/30">
            <Link href="/chat" className="hover:text-white/70 transition-colors">App</Link>
            <Link href="/" className="hover:text-white/70 transition-colors">Home</Link>
            <span>© 2025 CampusQ. Not affiliated with Carleton University.</span>
          </div>
        </div>
      </footer>

    </div>
  )
}
