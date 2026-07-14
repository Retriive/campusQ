"use client"

import { useEffect, useRef, useState, type ReactNode } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { ArrowRight } from "lucide-react"
import { UniversityToggle } from "@/components/landing/university-toggle"
import { WaitlistCta } from "@/components/landing/waitlist-cta"
import { ThemeToggle, useLandingTheme } from "@/components/landing/theme"
import { landBody, landDisplay } from "@/components/landing/fonts"
import { SCHOOLS, schoolPath, type SchoolId } from "@/lib/landing-schools"

const STEPS = [
  { n: "01", title: "Ask", copy: "A real question in plain English — courses, prereqs, deadlines." },
  { n: "02", title: "Retrieve", copy: "CampusQ pulls from your university’s official calendar and rules." },
  { n: "03", title: "Answer", copy: "Accurate and sourced in seconds — not a forum thread from 2019." },
  { n: "04", title: "Intelligence", copy: "Every ask quietly maps anonymized demand for advising staff." },
]

function Reveal({
  children,
  delay = 0,
  className = "",
}: {
  children: ReactNode
  delay?: number
  className?: string
}) {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    el.classList.add("reveal")
    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          el.classList.add("is-visible")
          io.disconnect()
        }
      },
      { threshold: 0.15, rootMargin: "0px 0px -6% 0px" }
    )
    io.observe(el)
    return () => io.disconnect()
  }, [])
  return (
    <div ref={ref} className={className} style={delay ? { transitionDelay: `${delay}ms` } : undefined}>
      {children}
    </div>
  )
}

export function LandingPage({ defaultSchool = "carleton" }: { defaultSchool?: SchoolId }) {
  const router = useRouter()
  const [schoolId, setSchoolId] = useState<SchoolId>(defaultSchool)
  const school = SCHOOLS[schoolId]
  const { theme, toggle } = useLandingTheme()

  useEffect(() => {
    setSchoolId(defaultSchool)
  }, [defaultSchool])

  function selectSchool(id: SchoolId) {
    setSchoolId(id)
    const next = schoolPath(id)
    if (typeof window !== "undefined" && window.location.pathname !== next) {
      router.replace(next)
    }
  }

  return (
    <div className={`landing-track ${landDisplay.variable} ${landBody.variable} ${theme === "dark" ? "dark" : ""}`}>
      <div
        data-school={schoolId}
        className="min-h-screen bg-canvas text-ink flex flex-col [font-family:var(--land-body)] antialiased"
      >
        {/* ── Hero ─────────────────────────────────────────────────────── */}
        <header className="relative min-h-[100svh] flex flex-col">
          <div
            aria-hidden
            className="pointer-events-none absolute inset-0 bg-[linear-gradient(180deg,color-mix(in_oklab,var(--primary)_10%,var(--canvas))_0%,var(--canvas)_42%,var(--canvas)_100%)]"
          />

          <nav className="relative z-20 flex items-center justify-between gap-4 px-5 sm:px-8 lg:px-14 h-[4.25rem]">
            <Link href="/" className="[font-family:var(--land-display)] text-[1.35rem] tracking-[-0.02em]">
              Campus<span className="italic text-primary-ink">Q</span>
            </Link>
            <div className="flex items-center gap-3 sm:gap-4">
              <div className="hidden lg:block">
                <UniversityToggle activeId={schoolId} onSelect={selectSchool} />
              </div>
              <Link href="/about" className="hidden sm:inline text-sm text-ink-body hover:text-ink transition-colors">
                About
              </Link>
              <ThemeToggle theme={theme} onToggle={toggle} />
              {school.live ? (
                <Link
                  href="/chat"
                  className="land-press inline-flex items-center gap-1.5 rounded-md bg-ink px-3.5 py-2 text-sm font-semibold text-canvas"
                >
                  Open app
                </Link>
              ) : null}
            </div>
          </nav>

          <div className="relative z-10 flex-1 flex flex-col justify-center px-5 sm:px-8 lg:px-14 py-12 max-w-[1100px] w-full mx-auto">
            <p className="stagger-item text-[13px] font-semibold uppercase tracking-[0.14em] text-ink-faint">
              {school.badge}
            </p>

            <h1
              className="stagger-item mt-5 [font-family:var(--land-display)] text-[clamp(3.25rem,9vw,6.5rem)] leading-[0.95] tracking-[-0.03em]"
              style={{ animationDelay: "70ms" }}
            >
              Campus<span className="italic text-primary-ink">Q</span>
            </h1>

            <p
              className="stagger-item mt-6 max-w-2xl text-[clamp(1.2rem,2.4vw,1.65rem)] font-medium leading-snug tracking-[-0.02em] text-ink"
              style={{ animationDelay: "140ms" }}
            >
              Official answers for {school.shortName} students — and intelligence advisors can’t get anywhere else.
            </p>

            <p
              className="stagger-item mt-4 max-w-xl text-base sm:text-lg text-ink-body leading-relaxed"
              style={{ animationDelay: "210ms" }}
            >
              {school.live
                ? "Ask about courses, prerequisites, programs, and deadlines. Grounded in the official calendar."
                : `We’re indexing ${school.name}. Join the waitlist and we’ll email you the day it opens.`}
            </p>

            <div className="stagger-item mt-8" style={{ animationDelay: "280ms" }}>
              {school.live ? (
                <div className="flex flex-wrap items-center gap-4">
                  <Link
                    href="/chat"
                    className="land-press group inline-flex items-center gap-2 rounded-md bg-primary px-5 py-3 text-[15px] font-semibold text-primary-foreground"
                  >
                    Ask your first question
                    <ArrowRight className="size-4 transition-transform duration-200 ease-[var(--ease-land-out)] group-hover:translate-x-0.5" />
                  </Link>
                  <Link href="/sign-up" className="text-sm font-medium text-ink-body hover:text-ink transition-colors">
                    Create account
                  </Link>
                </div>
              ) : (
                <WaitlistCta school={school.shortName} />
              )}
            </div>

            <div className="mt-8 lg:hidden">
              <UniversityToggle activeId={schoolId} onSelect={selectSchool} />
            </div>
          </div>

          {/* Product plane — edge to edge, no fake browser chrome */}
          <div className="relative z-10 border-t border-line bg-canvas-raised">
            <div className="max-w-[1100px] mx-auto px-5 sm:px-8 lg:px-14 py-8 sm:py-10">
              <div className="flex items-center justify-between gap-4 mb-6">
                <p className="text-[13px] font-semibold uppercase tracking-[0.14em] text-ink-faint">
                  {school.live ? `Live at ${school.shortName}` : `Coming to ${school.shortName}`}
                </p>
                <span className="text-[13px] text-ink-faint">{school.shortName}</span>
              </div>

              <div className="flex flex-col gap-3.5">
                {school.demoMessages.map((msg, i) => (
                  <div
                    key={`${schoolId}-${i}`}
                    className={`animate-message-in flex ${msg.role === "user" ? "justify-end" : "justify-start gap-3"}`}
                    style={{ animationDelay: `${i * 90}ms` }}
                  >
                    {msg.role === "assistant" && (
                      <div className="shrink-0 mt-1 size-7 rounded-md bg-primary text-primary-foreground text-[11px] font-bold flex items-center justify-center">
                        Q
                      </div>
                    )}
                    <div
                      className={`max-w-[90%] sm:max-w-[65%] text-[0.95rem] leading-relaxed px-4 py-3 rounded-2xl ${
                        msg.role === "user"
                          ? "bg-ink text-canvas rounded-br-md"
                          : "bg-canvas border border-line text-ink-body rounded-bl-md"
                      }`}
                    >
                      {msg.text}
                    </div>
                  </div>
                ))}
              </div>

              {school.live ? (
                <Link
                  href="/chat"
                  className="mt-7 flex items-center gap-3 rounded-md border border-line bg-canvas px-4 py-3.5 text-sm text-ink-faint hover:text-ink-body hover:border-ink/25 transition-[color,border-color] duration-200"
                >
                  <span className="flex-1 text-left">Ask anything about {school.shortName}…</span>
                  <span className="land-press size-9 rounded-md bg-ink text-canvas flex items-center justify-center">
                    <ArrowRight className="size-4" />
                  </span>
                </Link>
              ) : (
                <div className="mt-7 rounded-md border border-line bg-canvas px-4 py-3.5 text-sm text-ink-faint">
                  {school.shortName} catalog is being indexed…
                </div>
              )}
            </div>
          </div>
        </header>

        {/* ── Problem ──────────────────────────────────────────────────── */}
        <section className="border-t border-line">
          <div className="max-w-[1100px] mx-auto px-5 sm:px-8 lg:px-14 py-20 md:py-28 grid md:grid-cols-12 gap-10">
            <Reveal className="md:col-span-5">
              <p className="text-[13px] font-semibold uppercase tracking-[0.14em] text-ink-faint mb-4">The problem</p>
              <h2 className="[font-family:var(--land-display)] text-[clamp(2rem,4vw,3.1rem)] leading-[1.08] tracking-[-0.02em]">
                The information exists. <span className="italic text-primary-ink">It’s just buried.</span>
              </h2>
            </Reveal>
            <Reveal delay={80} className="md:col-span-6 md:col-start-7 flex flex-col gap-4 text-base sm:text-lg leading-relaxed text-ink-body md:pt-8">
              <p>
                Students waste hours jumping calendars, program pages, and advising inboxes for questions that should take thirty seconds.
              </p>
              <p>
                Advisors clear the same inbox every morning. CampusQ answers from official data — and quietly maps demand institutions can’t see.
              </p>
            </Reveal>
          </div>
        </section>

        {/* ── How it works ─────────────────────────────────────────────── */}
        <section className="border-t border-line bg-canvas-raised">
          <div className="max-w-[1100px] mx-auto px-5 sm:px-8 lg:px-14 py-20 md:py-28">
            <Reveal>
              <p className="text-[13px] font-semibold uppercase tracking-[0.14em] text-ink-faint mb-10">How it works</p>
            </Reveal>
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-x-8 gap-y-12">
              {STEPS.map((step, i) => (
                <Reveal key={step.n} delay={i * 70} className="border-t border-line pt-5">
                  <p className="[font-family:var(--land-display)] text-2xl text-primary-ink">{step.n}</p>
                  <h3 className="mt-3 text-base font-semibold tracking-tight">{step.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-ink-body">{step.copy}</p>
                </Reveal>
              ))}
            </div>
          </div>
        </section>

        {/* ── Stats ────────────────────────────────────────────────────── */}
        <section className="border-t border-line">
          <div className="max-w-[1100px] mx-auto px-5 sm:px-8 lg:px-14 py-16 md:py-20">
            {school.stats.length > 0 ? (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
                {school.stats.map((s, i) => (
                  <Reveal key={s.label} delay={i * 60} className="flex flex-col gap-1.5">
                    <span className="[font-family:var(--land-display)] text-4xl md:text-5xl tracking-[-0.03em] leading-none tabular-nums">
                      {s.value}
                    </span>
                    <span className="text-[12px] font-semibold uppercase tracking-[0.12em] text-ink-faint">{s.label}</span>
                  </Reveal>
                ))}
              </div>
            ) : (
              <Reveal>
                <p className="text-ink-body">
                  <span className="text-ink font-semibold">{school.shortName}</span> is being indexed — join the waitlist to get notified first.
                </p>
              </Reveal>
            )}
          </div>
        </section>

        {/* ── Close ────────────────────────────────────────────────────── */}
        <section className="border-t border-line">
          <div className="max-w-[1100px] mx-auto px-5 sm:px-8 lg:px-14 py-24 md:py-28">
            <Reveal>
              <h2 className="[font-family:var(--land-display)] text-[clamp(2.25rem,5vw,4rem)] leading-[1.05] tracking-[-0.025em] max-w-3xl">
                {school.live ? "Your questions, answered instantly." : `${school.shortName} is next.`}
              </h2>
              <p className="mt-5 text-lg text-ink-body max-w-xl leading-relaxed">
                {school.live
                  ? "No advisor queue. No calendar rabbit holes. Just ask."
                  : `We’re indexing ${school.shortName} now. Join the waitlist and we’ll email you the day it opens.`}
              </p>
              <div className="mt-8">
                {school.live ? (
                  <Link
                    href="/chat"
                    className="land-press group inline-flex items-center gap-2 rounded-md bg-ink px-5 py-3 text-[15px] font-semibold text-canvas"
                  >
                    Open CampusQ free
                    <ArrowRight className="size-4 transition-transform duration-200 ease-[var(--ease-land-out)] group-hover:translate-x-0.5" />
                  </Link>
                ) : (
                  <WaitlistCta school={school.shortName} />
                )}
              </div>
              <p className="mt-8 text-xs text-ink-faint">Not affiliated with {school.name}</p>
            </Reveal>
          </div>
        </section>

        <footer className="border-t border-line px-5 sm:px-8 lg:px-14 py-10 mt-auto">
          <div className="max-w-[1100px] mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-5">
            <div className="flex items-center gap-3">
              <span className="[font-family:var(--land-display)] text-lg tracking-tight">
                Campus<span className="italic text-primary-ink">Q</span>
              </span>
              <span className="text-ink-faint/40">·</span>
              <a href="https://retriive.com" className="text-xs text-link-muted hover:text-ink transition-colors">
                by Retriive
              </a>
            </div>
            <div className="flex flex-wrap gap-x-6 gap-y-2 text-xs text-link-muted">
              <Link href="/chat" className="hover:text-ink transition-colors">App</Link>
              <Link href="/about" className="hover:text-ink transition-colors">About</Link>
              <Link href="/privacy" className="hover:text-ink transition-colors">Privacy</Link>
              <a href="mailto:hello@retriive.com" className="hover:text-ink transition-colors">Contact</a>
            </div>
          </div>
        </footer>
      </div>
    </div>
  )
}
