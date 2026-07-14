"use client"

import { useEffect, useRef, useState, type ReactNode } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { ArrowRight } from "lucide-react"
import { UniversityToggle } from "@/components/landing/university-toggle"
import { WaitlistCta } from "@/components/landing/waitlist-cta"
import { ThemeToggle, useLandingTheme } from "@/components/landing/theme"
import { landBody, landDisplay } from "@/components/landing/fonts"
import { LandingParticles } from "@/components/landing/landing-particles"
import { SCHOOLS, schoolPath, type SchoolId } from "@/lib/landing-schools"

// Ink & Signal — marketing motion is first-visit delight: masked brand reveal,
// orchestrated stagger, directional demo cascade, clip-path stage, scroll
// reveals, number tickers. Craft bar: .agents/skills/emil-design-eng

const STEPS = [
  { n: "01", title: "Ask", copy: "A real question in plain English — courses, prereqs, deadlines." },
  { n: "02", title: "Retrieve", copy: "CampusQ pulls from your university’s official calendar and rules." },
  { n: "03", title: "Answer", copy: "Accurate, sourced, in seconds — not a Reddit thread from 2019." },
  { n: "04", title: "Intelligence", copy: "Every ask quietly feeds anonymized demand insights for advisors." },
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
      { threshold: 0.12, rootMargin: "0px 0px -8% 0px" }
    )
    io.observe(el)
    return () => io.disconnect()
  }, [])
  return (
    <div
      ref={ref}
      className={className}
      style={delay ? { transitionDelay: `${delay}ms` } : undefined}
    >
      {children}
    </div>
  )
}

/** Number ticker — rolls digits when the parent reveal becomes visible. */
function StatValue({ value }: { value: string }) {
  const ref = useRef<HTMLSpanElement>(null)
  const [display, setDisplay] = useState(value)
  const numeric = /^[\d,]+$/.test(value)

  useEffect(() => {
    if (!numeric) {
      setDisplay(value)
      return
    }
    const el = ref.current
    if (!el) return
    const target = Number(value.replace(/,/g, ""))
    let raf = 0
    let started = false

    const tick = (t0: number) => {
      const step = (now: number) => {
        const p = Math.min(1, (now - t0) / 900)
        const e = 1 - Math.pow(1 - p, 4)
        setDisplay(Math.round(target * e).toLocaleString("en-US"))
        if (p < 1) raf = requestAnimationFrame(step)
      }
      raf = requestAnimationFrame(step)
    }

    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !started) {
          started = true
          setDisplay("0")
          tick(performance.now())
          io.disconnect()
        }
      },
      { threshold: 0.4 }
    )
    io.observe(el)
    return () => {
      io.disconnect()
      cancelAnimationFrame(raf)
    }
  }, [value, numeric])

  return (
    <span ref={ref} className="land-tick tabular-nums">
      {display}
    </span>
  )
}

export function LandingPage({ defaultSchool = "carleton" }: { defaultSchool?: SchoolId }) {
  const router = useRouter()
  const [schoolId, setSchoolId] = useState<SchoolId>(defaultSchool)
  const [demoKey, setDemoKey] = useState(0)
  const school = SCHOOLS[schoolId]
  const { theme, toggle } = useLandingTheme()

  useEffect(() => {
    setSchoolId(defaultSchool)
  }, [defaultSchool])

  function selectSchool(id: SchoolId) {
    setSchoolId(id)
    setDemoKey((k) => k + 1)
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
        <header className="relative min-h-[100svh] flex flex-col overflow-hidden">
          <div aria-hidden className="pointer-events-none absolute inset-0">
            <div className="absolute inset-0 bg-[radial-gradient(120%_80%_at_10%_-10%,color-mix(in_oklab,var(--primary)_28%,transparent),transparent_55%),radial-gradient(90%_70%_at_100%_10%,color-mix(in_oklab,var(--primary)_16%,transparent),transparent_50%),linear-gradient(180deg,var(--canvas)_0%,color-mix(in_oklab,var(--canvas)_70%,var(--primary-soft))_100%)]" />
            <div className="land-mesh absolute -left-[20%] top-[18%] size-[58vmin] rounded-full bg-[radial-gradient(circle,color-mix(in_oklab,var(--primary)_35%,transparent),transparent_68%)] blur-xl opacity-80" />
            <div
              className="land-mesh absolute -right-[15%] top-[40%] size-[48vmin] rounded-full bg-[radial-gradient(circle,color-mix(in_oklab,var(--primary-ink)_22%,transparent),transparent_70%)] blur-xl opacity-70"
              style={{ animationDelay: "-4s" }}
            />
            <div
              className="land-mesh absolute left-[35%] -bottom-[10%] size-[42vmin] rounded-full bg-[radial-gradient(circle,color-mix(in_oklab,var(--primary)_18%,transparent),transparent_70%)] blur-xl opacity-50"
              style={{ animationDelay: "-8s" }}
            />
            <LandingParticles className="opacity-80 dark:opacity-90" />
            <div
              className="absolute inset-0 opacity-[0.28] mix-blend-multiply dark:mix-blend-soft-light dark:opacity-[0.2]"
              style={{
                backgroundImage:
                  "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.55'/%3E%3C/svg%3E\")",
              }}
            />
          </div>

          <nav className="relative z-20 flex items-center justify-between gap-4 px-5 sm:px-8 lg:px-12 h-16 sm:h-[4.25rem]">
            <Link
              href="/"
              className="[font-family:var(--land-display)] text-[1.15rem] font-bold tracking-[-0.03em]"
            >
              Campus<span className="text-primary-ink">Q</span>
            </Link>
            <div className="flex items-center gap-2 sm:gap-3">
              <div className="hidden md:block">
                <UniversityToggle activeId={schoolId} onSelect={selectSchool} />
              </div>
              <Link
                href="/about"
                className="hidden sm:inline text-sm text-ink-body hover:text-ink transition-colors duration-200"
              >
                About
              </Link>
              <ThemeToggle theme={theme} onToggle={toggle} />
              {school.live ? (
                <Link
                  href="/chat"
                  className="land-press inline-flex items-center gap-1.5 rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground"
                >
                  Open app
                </Link>
              ) : null}
            </div>
          </nav>

          <div className="relative z-10 flex-1 flex flex-col justify-end px-5 sm:px-8 lg:px-12 pb-8 sm:pb-10 pt-10 max-w-[1400px] w-full mx-auto">
            <p className="land-brand [font-family:var(--land-display)] text-[clamp(3.4rem,12vw,8.5rem)] font-extrabold leading-[0.88] tracking-[-0.055em] text-balance">
              Campus<span className="text-primary-ink">Q</span>
            </p>

            <h1
              className="stagger-item mt-5 sm:mt-6 max-w-3xl text-[clamp(1.35rem,3.2vw,2.35rem)] font-semibold leading-[1.15] tracking-[-0.03em] text-balance"
              style={{ animationDelay: "220ms" }}
            >
              Official answers for {school.shortName} students — advisors get their time back.
            </h1>

            <p
              className="stagger-item mt-4 max-w-xl text-base sm:text-lg text-ink-body leading-relaxed"
              style={{ animationDelay: "360ms" }}
            >
              {school.live
                ? "Ask about courses, prerequisites, programs, and deadlines. Sourced from the official calendar."
                : `CampusQ is indexing ${school.name}. Join the waitlist and we’ll email you the day it opens.`}
            </p>

            <div className="stagger-item mt-7" style={{ animationDelay: "500ms" }}>
              {school.live ? (
                <div className="flex flex-wrap items-center gap-4">
                  <Link
                    href="/chat"
                    className="land-press group inline-flex items-center gap-2 rounded-xl bg-ink px-6 py-3.5 text-base font-semibold text-canvas"
                  >
                    Ask your first question
                    <ArrowRight className="land-arrow size-4" />
                  </Link>
                  <Link
                    href="/sign-up"
                    className="text-sm font-medium text-ink-body hover:text-ink transition-colors duration-200"
                  >
                    Create account
                  </Link>
                </div>
              ) : (
                <WaitlistCta school={school.shortName} />
              )}
            </div>

            <div className="mt-6 md:hidden">
              <UniversityToggle activeId={schoolId} onSelect={selectSchool} />
            </div>
          </div>

          <div className="relative z-10 land-clip-reveal border-t border-line bg-canvas-raised/80 backdrop-blur-[2px]">
            <div className="max-w-[1400px] mx-auto px-5 sm:px-8 lg:px-12 py-7 sm:py-9">
              <div className="flex items-center gap-3 mb-6">
                <span className="relative flex size-2.5">
                  <span
                    className={`absolute inset-0 rounded-sm bg-primary ${school.live ? "land-pulse" : ""}`}
                  />
                  <span className="relative size-2.5 rounded-sm bg-primary" />
                </span>
                <span className="text-xs font-medium uppercase tracking-[0.14em] text-ink-faint">
                  {school.live ? `Live · ${school.shortName}` : `Coming · ${school.shortName}`}
                </span>
              </div>
              <div key={`${schoolId}-${demoKey}`} className="flex flex-col gap-4 min-h-[200px] sm:min-h-[220px]">
                {school.demoMessages.map((msg, i) => (
                  <div
                    key={`${schoolId}-${demoKey}-${i}`}
                    className={`flex ${msg.role === "user" ? "justify-end land-msg-user" : "justify-start gap-3 land-msg-assistant"}`}
                    style={{ animationDelay: `${650 + i * 140}ms` }}
                  >
                    {msg.role === "assistant" && (
                      <div className="shrink-0 size-7 rounded-lg bg-primary flex items-center justify-center text-[10px] font-bold text-primary-foreground mt-0.5">
                        Q
                      </div>
                    )}
                    <div
                      className={`max-w-[88%] sm:max-w-[62%] text-[0.9375rem] leading-relaxed px-4 py-3 ${
                        msg.role === "user"
                          ? "bg-ink text-canvas rounded-2xl rounded-br-md"
                          : "bg-canvas text-ink-body border border-line rounded-2xl rounded-bl-md"
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
                  className="mt-6 flex items-center gap-3 rounded-xl border border-line bg-canvas px-5 py-3.5 text-sm text-ink-faint hover:text-ink-body hover:border-ink-faint transition-[color,border-color] duration-200"
                >
                  <span className="flex-1 text-left">Ask anything about {school.shortName}…</span>
                  <span className="land-press size-9 rounded-lg bg-primary flex items-center justify-center">
                    <ArrowRight className="size-4 text-primary-foreground" />
                  </span>
                </Link>
              ) : (
                <div className="mt-6 rounded-xl border border-line bg-canvas px-5 py-3.5 text-sm text-ink-faint">
                  {school.shortName} catalog indexing…
                </div>
              )}
            </div>
          </div>
        </header>

        <section className="border-t border-line">
          <div className="max-w-[1400px] mx-auto px-5 sm:px-8 lg:px-12 py-20 md:py-28 grid grid-cols-1 md:grid-cols-12 gap-10">
            <Reveal className="md:col-span-5">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-ink-faint mb-5">
                The problem
              </p>
              <h2 className="[font-family:var(--land-display)] text-[clamp(2rem,4.5vw,3.5rem)] font-bold leading-[1.05] tracking-[-0.04em] text-balance">
                The information exists.
                <span className="text-primary-ink"> It’s just buried.</span>
              </h2>
            </Reveal>
            <Reveal delay={120} className="md:col-span-6 md:col-start-7 flex flex-col gap-5 text-base sm:text-lg leading-relaxed text-ink-body md:pt-10">
              <p>
                Students burn hours jumping calendars, program pages, and advising inboxes for questions that should take thirty seconds.
              </p>
              <p>
                Advisors spend mornings clearing the same inbox. CampusQ answers students from official data — and quietly maps the demand institutions can’t see.
              </p>
            </Reveal>
          </div>
        </section>

        <section className="border-t border-line bg-canvas-raised">
          <div className="max-w-[1400px] mx-auto px-5 sm:px-8 lg:px-12 py-20 md:py-28">
            <Reveal>
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-ink-faint mb-10">
                How it works
              </p>
            </Reveal>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-x-10 gap-y-12">
              {STEPS.map((step, i) => (
                <Reveal key={step.n} delay={i * 90} className="border-t border-line pt-6">
                  <p className="[font-family:var(--land-display)] text-3xl font-bold tabular-nums text-primary-ink tracking-tight">
                    {step.n}
                  </p>
                  <h3 className="mt-4 text-lg font-semibold tracking-tight">{step.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-ink-body">{step.copy}</p>
                </Reveal>
              ))}
            </div>
          </div>
        </section>

        <section className="border-t border-line">
          <div className="max-w-[1400px] mx-auto px-5 sm:px-8 lg:px-12 py-16 md:py-20">
            {school.stats.length > 0 ? (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-x-6 gap-y-10">
                {school.stats.map((s, i) => (
                  <Reveal key={`${schoolId}-${s.label}`} delay={i * 80} className="flex flex-col gap-2">
                    <span className="[font-family:var(--land-display)] text-4xl md:text-5xl font-bold tracking-[-0.04em] leading-none">
                      <StatValue value={s.value} />
                    </span>
                    <span className="text-xs font-semibold uppercase tracking-[0.14em] text-ink-faint">
                      {s.label}
                    </span>
                  </Reveal>
                ))}
              </div>
            ) : (
              <Reveal>
                <p className="text-ink-body">
                  <span className="text-ink font-semibold">{school.shortName}</span> is being indexed —
                  join the waitlist to get notified first.
                </p>
              </Reveal>
            )}
          </div>
        </section>

        <section className="border-t border-line relative overflow-hidden">
          <div
            aria-hidden
            className="pointer-events-none absolute inset-0 bg-[radial-gradient(80%_120%_at_50%_120%,color-mix(in_oklab,var(--primary)_22%,transparent),transparent_60%)]"
          />
          <div className="relative max-w-[1400px] mx-auto px-5 sm:px-8 lg:px-12 py-24 md:py-32">
            <Reveal>
              <p className="[font-family:var(--land-display)] text-[clamp(2.4rem,6vw,4.75rem)] font-extrabold leading-[0.95] tracking-[-0.05em] max-w-4xl text-balance">
                {school.live
                  ? "Your questions, answered instantly."
                  : `${school.shortName} is next.`}
              </p>
              <p className="mt-6 text-lg text-ink-body max-w-xl leading-relaxed">
                {school.live
                  ? "No advisor queue. No calendar rabbit holes. Just ask."
                  : `We’re indexing ${school.shortName} now. Join the waitlist and we’ll email you the day it opens.`}
              </p>
              <div className="mt-10">
                {school.live ? (
                  <Link
                    href="/chat"
                    className="land-press group inline-flex items-center gap-2 rounded-xl bg-primary px-7 py-3.5 text-base font-semibold text-primary-foreground"
                  >
                    Open CampusQ free
                    <ArrowRight className="land-arrow size-4" />
                  </Link>
                ) : (
                  <WaitlistCta school={school.shortName} />
                )}
              </div>
              <p className="mt-8 text-xs text-ink-faint">Not affiliated with {school.name}</p>
            </Reveal>
          </div>
        </section>

        <footer className="border-t border-line px-5 sm:px-8 lg:px-12 py-12 mt-auto">
          <div className="max-w-[1400px] mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
            <div className="flex items-center gap-3">
              <span className="[font-family:var(--land-display)] font-bold tracking-tight">
                Campus<span className="text-primary-ink">Q</span>
              </span>
              <span className="text-ink-faint/40">·</span>
              <a
                href="https://retriive.com"
                className="text-xs text-link-muted underline underline-offset-2 hover:text-ink transition-colors"
              >
                by Retriive
              </a>
            </div>
            <div className="flex flex-wrap items-center gap-x-7 gap-y-3 text-xs">
              <Link href="/chat" className="text-link-muted hover:text-ink transition-colors">
                App
              </Link>
              <Link href="/about" className="text-link-muted hover:text-ink transition-colors">
                About
              </Link>
              <Link href="/privacy" className="text-link-muted hover:text-ink transition-colors">
                Privacy
              </Link>
              <a
                href="mailto:hello@retriive.com"
                className="text-link-muted hover:text-ink transition-colors"
              >
                Contact
              </a>
            </div>
          </div>
        </footer>
      </div>
    </div>
  )
}
