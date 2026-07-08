"use client"

import { useEffect, useRef, useState, type ReactNode } from "react"
import Link from "next/link"
import { ArrowRight } from "lucide-react"
import { UniversityToggle } from "@/components/landing/university-toggle"
import { WaitlistCta } from "@/components/landing/waitlist-cta"
import { ThemeToggle, useLandingTheme } from "@/components/landing/theme"
import { SCHOOLS, type SchoolId } from "@/lib/landing-schools"

// Dual-track landing (frontend/DESIGN.md): warm-cream transactional canvas by
// default, pure-black cinematic canvas in dark mode. Thin display type, pill
// CTAs, hairline dividers. The selected school's color family carries every
// accent via the [data-school] tokens in globals.css.

const STEPS = [
  "Student asks a question in plain English",
  "CampusQ retrieves the answer from your university's official calendar",
  "Student gets an accurate answer in seconds",
  "Advisor gets their time back",
]

// Scroll reveal: rise + fade the first time an element enters the viewport.
// The hiding class is added only after mount, so content stays visible
// without JavaScript, and prefers-reduced-motion renders it static (see
// .reveal in globals.css).
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
      { threshold: 0.15, rootMargin: "0px 0px -8% 0px" }
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
  const [schoolId, setSchoolId] = useState<SchoolId>(defaultSchool)
  const school = SCHOOLS[schoolId]
  const { theme, toggle } = useLandingTheme()

  return (
    <div className={`landing-track ${theme === "dark" ? "dark" : ""}`}>
    <div data-school={schoolId} className="min-h-screen bg-canvas text-ink flex flex-col [font-feature-settings:'ss03'] transition-colors duration-300">

      {/* Nav */}
      <nav className="sticky top-0 z-50 bg-canvas border-b border-line transition-colors duration-300">
        <div className="max-w-[1400px] mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-base tracking-tight">
              <span className="font-[550]">Campus</span><span className="font-[330] text-primary-ink transition-colors duration-500">Q</span>
            </span>
            {school.live && (
              <span className="text-[10px] tracking-[0.72px] uppercase px-2.5 py-0.5 rounded-full bg-primary text-primary-foreground transition-colors duration-500">
                Live
              </span>
            )}
          </div>
          <div className="flex items-center gap-4">
            <Link href="/about" className="text-sm text-ink-body hover:text-ink transition-colors hidden sm:block">
              About
            </Link>
            <ThemeToggle theme={theme} onToggle={toggle} />
            {school.live ? (
              <Link
                href="/sign-up"
                className="group inline-flex items-center gap-1.5 rounded-full bg-primary hover:bg-primary-strong px-5 py-2 text-sm text-primary-foreground pill-press"
              >
                Open app <ArrowRight className="size-3.5 transition-transform duration-200 ease-[var(--ease-out)] group-hover:translate-x-0.5" />
              </Link>
            ) : (
              <span className="text-xs text-ink-body border border-line rounded-full px-4 py-1.5">
                Coming soon
              </span>
            )}
          </div>
        </div>
      </nav>

      {/* Hero — one statement, extreme negative space. Orchestrated entrance:
          each block fades up in sequence (ease-out, plays once on mount). */}
      <section className="max-w-[1400px] w-full mx-auto px-6 pt-20 pb-16 md:pt-28 md:pb-24">
        <div className="mb-10 stagger-item">
          <UniversityToggle activeId={schoolId} onSelect={setSchoolId} />
        </div>

        <p className="text-xs uppercase tracking-[0.72px] text-ink-faint mb-6 stagger-item" style={{ animationDelay: "60ms" }}>
          {school.badge}
        </p>

        <h1 className="font-[330] leading-[1.04] tracking-[0.01em] text-[clamp(2.75rem,7vw,5.5rem)] text-balance max-w-5xl stagger-item" style={{ animationDelay: "120ms" }}>
          The academic intelligence layer for{" "}
          <span className="text-primary-ink transition-colors duration-500">every university.</span>
        </h1>

        <p className="mt-8 text-xl md:text-2xl font-[330] leading-snug text-ink-body max-w-2xl stagger-item" style={{ animationDelay: "200ms" }}>
          Students get answers. <span className="text-ink">Advisors get their time back.</span>
        </p>

        <div className="mt-10 stagger-item" style={{ animationDelay: "280ms" }}>
          {school.live ? (
            <div className="flex flex-wrap items-center gap-6">
              <Link
                href="/sign-up"
                className="group inline-flex items-center gap-2 rounded-full bg-primary hover:bg-primary-strong px-7 py-3 text-base text-primary-foreground pill-press"
              >
                Ask your first question
                <ArrowRight className="size-4 transition-transform duration-200 ease-[var(--ease-out)] group-hover:translate-x-0.5" />
              </Link>
              <Link href="/about" className="text-sm text-ink-body hover:text-ink transition-colors">
                Learn more →
              </Link>
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              <p className="text-sm text-ink-body">
                CampusQ is coming to {school.shortName}. Drop your email and we&apos;ll tell you the moment it&apos;s ready.
              </p>
              <WaitlistCta school={school.shortName} />
            </div>
          )}
        </div>

        <p className="mt-7 text-xs text-ink-faint stagger-item" style={{ animationDelay: "340ms" }}>
          {school.live
            ? `Free to sign up · Built on official ${school.shortName} documents`
            : `Not affiliated with ${school.name}`}
        </p>
      </section>

      {/* Product frame — the mockup is the photography. Arrives last in the
          hero sequence, after the copy has landed. */}
      <section className="max-w-[1400px] w-full mx-auto px-6 pb-24 md:pb-32 stagger-item" style={{ animationDelay: "420ms" }}>
        <div className="rounded-[20px] bg-canvas-raised border border-line overflow-hidden [box-shadow:var(--card-shadow)] transition-colors duration-300">
          {/* Window chrome */}
          <div className="border-b border-line px-5 py-3.5 flex items-center gap-2">
            <span className="size-2.5 rounded-full bg-ink-faint/30" />
            <span className="size-2.5 rounded-full bg-ink-faint/30" />
            <span className="size-2.5 rounded-full bg-ink-faint/30" />
            <div className="mx-auto flex items-center gap-2 rounded-full border border-line px-4 py-1">
              <span className="size-1.5 rounded-full bg-primary transition-colors duration-500" />
              <span className="text-[11px] text-ink-faint">campusq.retriive.com</span>
            </div>
            <span className="size-2.5 opacity-0" />
          </div>

          {/* Inner app nav */}
          <div className="px-5 py-3 border-b border-line flex items-center gap-2.5">
            <div className="size-5 rounded-md bg-primary flex items-center justify-center text-[9px] font-[550] text-primary-foreground transition-colors duration-500">
              Q
            </div>
            <span className="text-xs text-ink">CampusQ</span>
            <span className="ml-auto text-[10px] uppercase tracking-[0.72px] px-2 py-0.5 rounded-full border border-line text-primary-ink transition-colors duration-500">
              {school.shortName}
            </span>
          </div>

          {/* Messages — cascade in one after another; rows are keyed by school
              so switching universities replays the conversation. */}
          <div className="px-6 py-8 md:px-10 md:py-10 flex flex-col gap-5 min-h-[240px]">
            {school.demoMessages.map((msg, i) => (
              <div
                key={`${schoolId}-${i}`}
                className={`animate-message-in flex ${msg.role === "user" ? "justify-end" : "justify-start gap-3"}`}
                style={{ animationDelay: `${i * 160}ms` }}
              >
                {msg.role === "assistant" && (
                  <div className="shrink-0 size-6 rounded-full bg-primary flex items-center justify-center text-[9px] font-[550] text-primary-foreground mt-0.5 transition-colors duration-500">
                    Q
                  </div>
                )}
                <div className={`max-w-[80%] md:max-w-[60%] text-sm leading-relaxed rounded-2xl px-4 py-3 transition-colors duration-300 ${
                  msg.role === "user"
                    ? "bg-ink text-canvas rounded-br-sm"
                    : "bg-canvas text-ink-body rounded-bl-sm border border-line"
                }`}>
                  {msg.text}
                </div>
              </div>
            ))}
          </div>

          {/* Input */}
          <div className="border-t border-line px-5 py-4 flex items-center gap-3">
            {school.live ? (
              <>
                <Link href="/sign-up" className="flex-1 rounded-full border border-line px-5 py-3 text-xs text-ink-faint hover:border-ink-faint hover:text-ink-body transition-colors">
                  Ask anything about {school.shortName}…
                </Link>
                <Link href="/sign-up" className="size-10 rounded-full bg-primary hover:bg-primary-strong flex items-center justify-center shrink-0 pill-press">
                  <ArrowRight className="size-4 text-primary-foreground" />
                </Link>
              </>
            ) : (
              <div className="flex-1 rounded-full border border-line px-5 py-3 text-xs text-ink-faint">
                {school.shortName} coming soon…
              </div>
            )}
          </div>
        </div>
      </section>

      {/* The problem */}
      <section className="border-t border-line transition-colors duration-300">
        <div className="max-w-[1400px] mx-auto px-6 py-20 md:py-28 grid grid-cols-1 md:grid-cols-2 gap-10 items-start">
          <Reveal>
            <p className="text-xs uppercase tracking-[0.72px] text-ink-faint mb-6">The problem</p>
            <h2 className="font-[330] leading-[1.1] text-3xl md:text-5xl">
              There&apos;s a{" "}
              <span className="text-primary-ink transition-colors duration-500">better way.</span>
            </h2>
          </Reveal>
          <Reveal delay={120} className="flex flex-col gap-5 text-base leading-relaxed text-ink-body md:pt-12">
            <p>
              Students waste hours jumping between course calendars, program pages, and advising
              emails just to answer a simple question.
            </p>
            <p>
              Advisors spend their days answering the same ones over and over.
            </p>
          </Reveal>
        </div>
      </section>

      {/* The hero — advisor pull-quote band */}
      <section className="bg-primary-soft border-y border-primary-line/60 transition-colors duration-500">
        <div className="max-w-[1400px] mx-auto px-6 py-20 md:py-28">
          <Reveal>
            <p className="text-xs uppercase tracking-[0.72px] text-primary-ink mb-8 transition-colors duration-500">The hero</p>
            <p className="font-[330] leading-[1.2] text-2xl md:text-4xl max-w-4xl text-balance">
              Advisors who used to spend their mornings clearing inboxes now spend them with the
              students who actually need them.
            </p>
          </Reveal>
        </div>
      </section>

      {/* How it works */}
      <section className="max-w-[1400px] w-full mx-auto px-6 py-20 md:py-28">
        <Reveal>
          <p className="text-xs uppercase tracking-[0.72px] text-ink-faint mb-10">How it works</p>
        </Reveal>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-x-8 gap-y-10">
          {STEPS.map((step, i) => (
            <Reveal key={step} delay={i * 90} className="border-t border-line pt-6 flex flex-col gap-4 transition-colors duration-300">
              <span className="font-[330] text-3xl tabular-nums text-primary-ink transition-colors duration-500">
                0{i + 1}
              </span>
              <p className="text-base leading-relaxed text-ink-body">{step}</p>
            </Reveal>
          ))}
        </div>
      </section>

      {/* Stats band — giant thin numerals over hairlines */}
      <div className="border-y border-line transition-colors duration-300">
        <div className="max-w-[1400px] mx-auto px-6 py-12 md:py-16">
          {school.live ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-x-6 gap-y-10">
              {school.stats.map((s, i) => (
                <Reveal key={s.label} delay={i * 80} className="flex flex-col gap-2">
                  <span className="font-[330] text-4xl md:text-5xl tabular-nums leading-none">{s.value}</span>
                  <span className="text-xs uppercase tracking-[0.72px] text-ink-faint">{s.label}</span>
                </Reveal>
              ))}
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <span className="size-1.5 rounded-full bg-primary transition-colors duration-500" />
              <p className="text-sm text-ink-body">
                <span className="text-ink">{school.shortName}</span>&apos;s catalog is being indexed — join the waitlist to get notified first.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Closing CTA — one action, lots of air */}
      <section className="max-w-[1400px] w-full mx-auto px-6 py-28 md:py-40">
        <Reveal>
        <p className="text-xs uppercase tracking-[0.72px] text-ink-faint mb-6">
          {school.live ? "Get started free" : "Be first to know"}
        </p>
        <h2 className="font-[330] leading-[1.05] text-[clamp(2.25rem,5.5vw,4.375rem)] text-balance max-w-4xl">
          {school.live
            ? "Your questions, answered instantly."
            : `${school.shortName} is next on the list.`}
        </h2>
        <p className="mt-6 text-lg leading-[1.56] text-ink-body max-w-xl">
          {school.live
            ? "No advisor queue. No calendar rabbit holes. Just ask."
            : `We're indexing ${school.shortName}'s catalog now. Join the waitlist and we'll email you the day it opens.`}
        </p>

        <div className="mt-10">
          {school.live ? (
            <Link
              href="/sign-up"
              className="group inline-flex items-center gap-2 rounded-full bg-primary hover:bg-primary-strong px-7 py-3 text-base text-primary-foreground pill-press"
            >
              Open CampusQ free
              <ArrowRight className="size-4 transition-transform duration-200 ease-[var(--ease-out)] group-hover:translate-x-0.5" />
            </Link>
          ) : (
            <WaitlistCta school={school.shortName} />
          )}
        </div>

        <p className="mt-7 text-xs text-ink-faint">
          Not affiliated with {school.name}
        </p>
        </Reveal>
      </section>

      {/* Footer */}
      <footer className="border-t border-line px-6 py-16 mt-auto transition-colors duration-300">
        <div className="max-w-[1400px] mx-auto flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <span className="text-sm">
              <span className="font-[550]">Campus</span><span className="font-[330] text-primary-ink transition-colors duration-500">Q</span>
            </span>
            <span className="text-ink-faint/50">·</span>
            <a href="https://retriive.com" className="text-xs text-link-muted underline underline-offset-2 hover:text-ink transition-colors">
              by Retriive
            </a>
          </div>
          <div className="flex items-center gap-8 text-xs">
            <Link href="/chat" className="text-link-muted underline underline-offset-2 hover:text-ink transition-colors">App</Link>
            <Link href="/about" className="text-link-muted underline underline-offset-2 hover:text-ink transition-colors">About</Link>
            <a href="mailto:mahadmyonis@gmail.com" className="text-link-muted underline underline-offset-2 hover:text-ink transition-colors">Contact</a>
          </div>
        </div>
      </footer>

    </div>
    </div>
  )
}
