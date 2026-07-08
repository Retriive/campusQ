"use client"

import Link from "next/link"
import { ArrowRight, ShieldCheck, Mail } from "lucide-react"
import { ThemeToggle, useLandingTheme } from "@/components/landing/theme"

// Dots use each school's own accent token theme (see [data-school] in globals.css)
const SCHOOLS_STATUS = [
  { name: "Carleton University", short: "Carleton", status: "live" as const, school: "carleton" },
  { name: "University of Ottawa", short: "uOttawa", status: "soon" as const, school: "uottawa" },
  { name: "University of Toronto", short: "UofT", status: "soon" as const, school: "uoft" },
  { name: "University of Waterloo", short: "Waterloo", status: "soon" as const, school: "waterloo" },
  { name: "Western University", short: "Western", status: "soon" as const, school: "western" },
]

// Same dual-track visual system as the landing page (frontend/DESIGN.md).
export function AboutContent() {
  const { theme, toggle } = useLandingTheme()

  return (
    <div className={`landing-track ${theme === "dark" ? "dark" : ""}`}>
    <div data-school="carleton" className="min-h-screen bg-canvas text-ink flex flex-col [font-feature-settings:'ss03'] transition-colors duration-300">

      {/* Nav */}
      <nav className="sticky top-0 z-50 bg-canvas border-b border-line transition-colors duration-300">
        <div className="max-w-[1400px] mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="text-base tracking-tight">
            <span className="font-[550]">Campus</span><span className="font-[330] text-primary-ink">Q</span>
          </Link>
          <div className="flex items-center gap-4">
            <ThemeToggle theme={theme} onToggle={toggle} />
            <Link
              href="/chat"
              className="inline-flex items-center gap-1.5 rounded-full bg-primary hover:bg-primary-strong px-5 py-2 text-sm text-primary-foreground transition-colors"
            >
              Open app <ArrowRight className="size-3.5" />
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="border-b border-line transition-colors duration-300">
        <div className="max-w-[1400px] mx-auto px-6 pt-20 pb-16 md:pt-28 md:pb-24">
          <p className="text-xs uppercase tracking-[0.72px] text-ink-faint mb-6">About CampusQ</p>
          <h1 className="font-[330] leading-[1.05] text-[clamp(2.5rem,6vw,4.375rem)] text-balance max-w-3xl">
            Academic questions,<br />
            <span className="text-primary-ink">answered instantly.</span>
          </h1>
          <p className="mt-8 text-lg leading-[1.56] text-ink-body max-w-xl">
            CampusQ is an independent AI assistant built for Canadian university students. Ask anything
            about courses, prerequisites, programs, or deadlines — get a real answer in seconds, sourced
            directly from official university documents.
          </p>
        </div>
      </section>

      <main className="max-w-[1400px] mx-auto px-6 py-20 md:py-28 w-full flex flex-col gap-24 md:gap-32">

        {/* Why */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-10 items-start">
          <div>
            <p className="text-xs uppercase tracking-[0.72px] text-ink-faint mb-6">Why we built it</p>
            <h2 className="font-[330] leading-[1.14] text-3xl md:text-5xl">
              The information exists.<br />It&apos;s just inaccessible.
            </h2>
          </div>
          <div className="flex flex-col gap-5 text-base leading-relaxed text-ink-body">
            <p>
              Every semester, students waste hours cross-referencing PDFs, hunting for prerequisites,
              decoding program requirements, and waiting weeks for advisor appointments — to answer
              questions that should take 30 seconds.
            </p>
            <p>
              We index every course, program, academic regulation, tuition policy, and campus resource
              at each university — and build an AI that answers questions from it directly.
              No guessing. No Reddit threads from 2019.
            </p>
            <p>
              We&apos;re rolling out to every major Canadian university. Same idea, every campus.
            </p>
          </div>
        </section>

        {/* Schools */}
        <section>
          <p className="text-xs uppercase tracking-[0.72px] text-ink-faint mb-8">Where we&apos;re at</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {SCHOOLS_STATUS.map((s) => (
              <div
                key={s.name}
                data-school={s.school}
                className={`rounded-xl border border-line p-5 flex flex-col gap-3 transition-colors duration-300 ${
                  s.status === "live" ? "bg-canvas-raised [box-shadow:var(--card-shadow)]" : "bg-canvas"
                }`}
              >
                {/* color dot — takes this school's accent token */}
                <div className="size-2 rounded-full bg-primary" />
                <div>
                  <p className={`text-sm ${s.status === "live" ? "text-ink font-[550]" : "text-ink-body"}`}>
                    {s.name}
                  </p>
                </div>
                <div className="mt-auto">
                  {s.status === "live" ? (
                    <span className="inline-flex items-center gap-1.5 text-[10px] uppercase tracking-[0.72px] rounded-full bg-primary text-primary-foreground px-2.5 py-1">
                      Live
                    </span>
                  ) : (
                    <span className="text-[10px] uppercase tracking-[0.72px] text-ink-faint">
                      Coming soon
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Retriive — the company behind CampusQ */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-10 items-start">
          <div>
            <p className="text-xs uppercase tracking-[0.72px] text-ink-faint mb-6">The company behind it</p>
            <h2 className="font-[330] leading-[1.14] text-3xl md:text-5xl">
              CampusQ is built by <span className="text-primary-ink">Retriive</span>.
            </h2>
          </div>
          <div className="flex flex-col gap-5 text-base leading-relaxed text-ink-body">
            <p>
              Retriive builds AI solutions for institutions and enterprises — systems that
              <span className="text-ink"> eliminate informational silos</span> and
              <span className="text-ink"> optimize administrative efficiency</span> across
              an organization.
            </p>
            <p>
              The problem is the same everywhere: the answer already exists, but it&apos;s buried across PDFs,
              portals, inboxes, and people&apos;s heads — so the person who needs it can&apos;t find it. Retriive
              unifies that scattered knowledge and puts a precise, source-grounded answer one question away.
            </p>
            <p>
              CampusQ is that idea applied to universities — the first of many domains where Retriive turns
              fragmented information into instant, trustworthy answers.
            </p>
          </div>
        </section>

        {/* Disclaimer + Contact side by side */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="rounded-xl border border-line bg-canvas-raised [box-shadow:var(--card-shadow)] p-6 flex flex-col gap-3 transition-colors duration-300">
            <div className="flex items-center gap-2.5">
              <ShieldCheck className="size-4 text-ink-faint shrink-0" />
              <span className="text-sm font-[550] text-ink">Heads up</span>
            </div>
            <p className="text-sm leading-relaxed text-ink-body">
              CampusQ is an <span className="text-ink">independent tool</span> — not
              affiliated with, endorsed by, or operated by any university. Always verify important
              academic decisions with your advisor or official university sources.
            </p>
          </div>

          <div className="rounded-xl border border-line bg-canvas-raised [box-shadow:var(--card-shadow)] p-6 flex flex-col gap-3 transition-colors duration-300">
            <div className="flex items-center gap-2.5">
              <Mail className="size-4 text-ink-faint shrink-0" />
              <span className="text-sm font-[550] text-ink">Get in touch</span>
            </div>
            <p className="text-sm leading-relaxed text-ink-body">
              Found an error, have feedback, or want to bring CampusQ to your school?
            </p>
            <a
              href="mailto:team@retriive.com"
              className="mt-auto inline-flex items-center gap-1.5 text-sm text-ink hover:text-primary-ink transition-colors"
            >
              team@retriive.com <ArrowRight className="size-3.5" />
            </a>
          </div>
        </section>

      </main>

      {/* Footer */}
      <footer className="border-t border-line px-6 py-16 mt-auto transition-colors duration-300">
        <div className="max-w-[1400px] mx-auto flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <Link href="/" className="text-sm">
              <span className="font-[550]">Campus</span><span className="font-[330] text-primary-ink">Q</span>
            </Link>
            <span className="text-ink-faint/50">·</span>
            <a href="https://retriive.com" className="text-xs text-link-muted underline underline-offset-2 hover:text-ink transition-colors">
              by Retriive
            </a>
          </div>
          <span className="text-xs text-ink-faint">Not affiliated with any university</span>
        </div>
      </footer>

    </div>
    </div>
  )
}
