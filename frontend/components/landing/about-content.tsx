"use client"

import Link from "next/link"
import { ArrowRight, ShieldCheck, Mail } from "lucide-react"
import { ThemeToggle, useLandingTheme } from "@/components/landing/theme"
import { landBody, landDisplay } from "@/components/landing/fonts"

// Dots use each school's own accent token theme (see [data-school] in globals.css)
const SCHOOLS_STATUS = [
  { name: "Carleton University", short: "Carleton", status: "live" as const, school: "carleton", href: "/" },
  { name: "University of Ottawa", short: "uOttawa", status: "soon" as const, school: "uottawa", href: "/uottawa" },
  { name: "University of Toronto", short: "UofT", status: "soon" as const, school: "uoft", href: "/uoft" },
  { name: "University of Waterloo", short: "Waterloo", status: "soon" as const, school: "waterloo", href: "/waterloo" },
  { name: "Western University", short: "Western", status: "soon" as const, school: "western", href: "/western" },
  { name: "McGill University", short: "McGill", status: "soon" as const, school: "mcgill", href: "/mcgill" },
]

// Matches the current landing type system.
export function AboutContent() {
  const { theme, toggle } = useLandingTheme()

  return (
    <div className={`landing-track ${landDisplay.variable} ${landBody.variable} ${theme === "dark" ? "dark" : ""}`}>
    <div data-school="carleton" className="min-h-screen bg-canvas text-ink flex flex-col [font-family:var(--land-body)] antialiased">

      <nav className="sticky top-0 z-50 bg-canvas border-b border-line">
        <div className="max-w-[1100px] mx-auto px-5 sm:px-8 lg:px-14 h-[4.25rem] flex items-center justify-between">
          <Link href="/" className="[font-family:var(--land-display)] text-[1.35rem] tracking-[-0.02em]">
            Campus<span className="italic text-primary-ink">Q</span>
          </Link>
          <div className="flex items-center gap-4">
            <ThemeToggle theme={theme} onToggle={toggle} />
            <Link
              href="/chat"
              className="land-press inline-flex items-center gap-1.5 rounded-md bg-ink px-3.5 py-2 text-sm font-semibold text-canvas"
            >
              Open app <ArrowRight className="size-3.5" />
            </Link>
          </div>
        </div>
      </nav>

      <section className="border-b border-line">
        <div className="max-w-[1100px] mx-auto px-5 sm:px-8 lg:px-14 pt-20 pb-16 md:pt-28 md:pb-24">
          <p className="text-[13px] font-semibold uppercase tracking-[0.14em] text-ink-faint mb-5">About CampusQ</p>
          <h1 className="[font-family:var(--land-display)] leading-[1.05] tracking-[-0.025em] text-[clamp(2.5rem,6vw,4.25rem)] text-balance max-w-3xl">
            Academic questions,<br />
            <span className="italic text-primary-ink">answered instantly.</span>
          </h1>
          <p className="mt-7 text-lg leading-relaxed text-ink-body max-w-xl">
            CampusQ is an independent AI assistant built for Canadian university students. Ask anything
            about courses, prerequisites, programs, or deadlines — get a real answer in seconds, sourced
            directly from official university documents.
          </p>
        </div>
      </section>

      <main className="max-w-[1100px] mx-auto px-5 sm:px-8 lg:px-14 py-20 md:py-28 w-full flex flex-col gap-24 md:gap-28">

        <section className="grid grid-cols-1 md:grid-cols-2 gap-10 items-start">
          <div>
            <p className="text-[13px] font-semibold uppercase tracking-[0.14em] text-ink-faint mb-5">Why we built it</p>
            <h2 className="[font-family:var(--land-display)] leading-[1.1] tracking-[-0.02em] text-[clamp(1.85rem,3.5vw,2.75rem)]">
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

        <section>
          <p className="text-[13px] font-semibold uppercase tracking-[0.14em] text-ink-faint mb-8">Where we&apos;re at</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {SCHOOLS_STATUS.map((s) => (
              <Link
                key={s.name}
                href={s.href}
                data-school={s.school}
                className={`rounded-md border border-line p-5 flex flex-col gap-3 transition-colors hover:border-ink/25 ${
                  s.status === "live" ? "bg-canvas-raised" : "bg-canvas"
                }`}
              >
                <div className="size-2 rounded-sm bg-primary" />
                <p className={`text-sm ${s.status === "live" ? "text-ink font-semibold" : "text-ink-body"}`}>
                  {s.name}
                </p>
                <div className="mt-auto">
                  {s.status === "live" ? (
                    <span className="inline-flex text-[10px] uppercase tracking-[0.12em] rounded-md bg-primary text-primary-foreground px-2 py-1">
                      Live
                    </span>
                  ) : (
                    <span className="text-[10px] uppercase tracking-[0.12em] text-ink-faint">
                      Join waitlist →
                    </span>
                  )}
                </div>
              </Link>
            ))}
          </div>
        </section>

        <section className="grid grid-cols-1 md:grid-cols-2 gap-10 items-start">
          <div>
            <p className="text-[13px] font-semibold uppercase tracking-[0.14em] text-ink-faint mb-5">The company behind it</p>
            <h2 className="[font-family:var(--land-display)] leading-[1.1] tracking-[-0.02em] text-[clamp(1.85rem,3.5vw,2.75rem)]">
              CampusQ is built by <span className="italic text-primary-ink">Retriive</span>.
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

        <section className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="rounded-md border border-line bg-canvas-raised p-6 flex flex-col gap-3">
            <div className="flex items-center gap-2.5">
              <ShieldCheck className="size-4 text-ink-faint shrink-0" />
              <span className="text-sm font-semibold text-ink">Heads up</span>
            </div>
            <p className="text-sm leading-relaxed text-ink-body">
              CampusQ is an <span className="text-ink">independent tool</span> — not
              affiliated with, endorsed by, or operated by any university. Always verify important
              academic decisions with your advisor or official university sources.
            </p>
          </div>

          <div className="rounded-md border border-line bg-canvas-raised p-6 flex flex-col gap-3">
            <div className="flex items-center gap-2.5">
              <Mail className="size-4 text-ink-faint shrink-0" />
              <span className="text-sm font-semibold text-ink">Get in touch</span>
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

      <footer className="border-t border-line px-5 sm:px-8 lg:px-14 py-10 mt-auto">
        <div className="max-w-[1100px] mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-5">
          <div className="flex items-center gap-3">
            <Link href="/" className="[font-family:var(--land-display)] text-lg tracking-tight">
              Campus<span className="italic text-primary-ink">Q</span>
            </Link>
            <span className="text-ink-faint/40">·</span>
            <a href="https://retriive.com" className="text-xs text-link-muted hover:text-ink transition-colors">
              by Retriive
            </a>
          </div>
          <div className="flex items-center gap-6 text-xs text-link-muted">
            <Link href="/privacy" className="hover:text-ink transition-colors">Privacy</Link>
            <a href="mailto:hello@retriive.com" className="hover:text-ink transition-colors">Contact</a>
          </div>
        </div>
      </footer>

    </div>
    </div>
  )
}
