"use client"

import { useState } from "react"
import Link from "next/link"
import { ArrowRight } from "lucide-react"
import { UniversityToggle } from "@/components/landing/university-toggle"
import { WaitlistCta } from "@/components/landing/waitlist-cta"
import { SCHOOLS, type SchoolId } from "@/lib/landing-schools"

// Cinematic-track landing (frontend/DESIGN.md): pure black canvas, thin-weight
// display type, white-stroked pill CTAs, one action per band, flat blackness.

export function LandingPage({ defaultSchool = "carleton" }: { defaultSchool?: SchoolId }) {
  const [schoolId, setSchoolId] = useState<SchoolId>(defaultSchool)
  const school = SCHOOLS[schoolId]

  return (
    <div className="min-h-screen bg-night text-white flex flex-col [font-feature-settings:'ss03']">

      {/* Nav — nav-bar-dark */}
      <nav className="sticky top-0 z-50 bg-night border-b border-night-line">
        <div className="max-w-[1400px] mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-base tracking-tight">
              <span className="font-[550]">Campus</span><span className="font-[330]">Q</span>
            </span>
            {school.live && (
              <span className="text-[10px] tracking-[0.72px] uppercase px-2.5 py-0.5 rounded-full border border-white/30 text-zinc-300">
                Live
              </span>
            )}
          </div>
          <div className="flex items-center gap-6">
            <Link href="/about" className="text-sm text-zinc-400 hover:text-white transition-colors hidden sm:block">
              About
            </Link>
            {school.live ? (
              <Link
                href="/sign-up"
                className="inline-flex items-center gap-1.5 rounded-full border-2 border-white px-5 py-1.5 text-sm text-white hover:bg-white hover:text-black transition-colors"
              >
                Open app <ArrowRight className="size-3.5" />
              </Link>
            ) : (
              <span className="text-xs text-zinc-400 border border-night-line rounded-full px-4 py-1.5">
                Coming soon
              </span>
            )}
          </div>
        </div>
      </nav>

      {/* Hero — one statement, extreme negative space */}
      <section className="max-w-[1400px] w-full mx-auto px-6 pt-20 pb-16 md:pt-28 md:pb-24">
        <div className="mb-10">
          <UniversityToggle activeId={schoolId} onSelect={setSchoolId} />
        </div>

        <p className="text-xs uppercase tracking-[0.72px] text-zinc-400 mb-6">
          {school.badge}
        </p>

        <h1 className="font-[330] leading-[1.02] tracking-[0.02em] text-[clamp(2.9rem,8vw,6rem)] text-balance max-w-5xl">
          Every answer your advisor would give.{" "}
          <span className="text-zinc-500">In seconds.</span>
        </h1>

        <p className="mt-8 text-lg leading-[1.56] text-zinc-400 max-w-xl">
          {school.live
            ? "Prerequisites, deadlines, degree requirements — answered from official university documents, with sources you can check."
            : `CampusQ is coming to ${school.shortName}. Drop your email and we'll tell you the moment it's ready.`}
        </p>

        <div className="mt-10">
          {school.live ? (
            <div className="flex flex-wrap items-center gap-6">
              <Link
                href="/sign-up"
                className="inline-flex items-center gap-2 rounded-full border-2 border-white px-7 py-3 text-base text-white hover:bg-white hover:text-black transition-colors"
              >
                Ask your first question
                <ArrowRight className="size-4" />
              </Link>
              <Link href="/about" className="text-sm text-zinc-400 hover:text-white transition-colors">
                Learn more →
              </Link>
            </div>
          ) : (
            <WaitlistCta school={school.shortName} />
          )}
        </div>

        <p className="mt-7 text-xs text-zinc-500">
          {school.live
            ? `Free to sign up · Built on official ${school.shortName} documents`
            : `Not affiliated with ${school.name}`}
        </p>
      </section>

      {/* Product frame — card-photo-frame: the mockup is the photography */}
      <section className="max-w-[1400px] w-full mx-auto px-6 pb-24 md:pb-32">
        <div className="rounded-[20px] bg-night-raised border border-night-line overflow-hidden [box-shadow:inset_0_1px_0_rgba(255,255,255,0.06)]">
          {/* Window chrome */}
          <div className="border-b border-night-line px-5 py-3.5 flex items-center gap-2">
            <span className="size-2.5 rounded-full bg-zinc-700" />
            <span className="size-2.5 rounded-full bg-zinc-700" />
            <span className="size-2.5 rounded-full bg-zinc-700" />
            <div className="mx-auto flex items-center gap-2 rounded-full border border-night-line px-4 py-1">
              <span className="size-1.5 rounded-full bg-white" />
              <span className="text-[11px] text-zinc-400">campusq.retriive.com</span>
            </div>
            <span className="size-2.5 opacity-0" />
          </div>

          {/* Inner app nav */}
          <div className="px-5 py-3 border-b border-night-line flex items-center gap-2.5">
            <div className="size-5 rounded-md bg-white flex items-center justify-center text-[9px] font-[550] text-black">
              Q
            </div>
            <span className="text-xs text-zinc-200">CampusQ</span>
            <span className="ml-auto text-[10px] uppercase tracking-[0.72px] px-2 py-0.5 rounded-full border border-night-line text-zinc-400">
              {school.shortName}
            </span>
          </div>

          {/* Messages */}
          <div className="px-6 py-8 md:px-10 md:py-10 flex flex-col gap-5 min-h-[240px]">
            {school.demoMessages.map((msg, i) => (
              <div key={`${schoolId}-${i}`} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start gap-3"}`}>
                {msg.role === "assistant" && (
                  <div className="shrink-0 size-6 rounded-full bg-white flex items-center justify-center text-[9px] font-[550] text-black mt-0.5">
                    Q
                  </div>
                )}
                <div className={`max-w-[80%] md:max-w-[60%] text-sm leading-relaxed rounded-2xl px-4 py-3 ${
                  msg.role === "user"
                    ? "bg-white text-black rounded-br-sm"
                    : "bg-white/[0.06] text-zinc-200 rounded-bl-sm border border-night-line"
                }`}>
                  {msg.text}
                </div>
              </div>
            ))}
          </div>

          {/* Input */}
          <div className="border-t border-night-line px-5 py-4 flex items-center gap-3">
            {school.live ? (
              <>
                <Link href="/sign-up" className="flex-1 rounded-full border border-night-line px-5 py-3 text-xs text-zinc-500 hover:border-zinc-500 hover:text-zinc-300 transition-colors">
                  Ask anything about {school.shortName}…
                </Link>
                <Link href="/sign-up" className="size-10 rounded-full border-2 border-white flex items-center justify-center shrink-0 hover:bg-white group transition-colors">
                  <ArrowRight className="size-4 text-white group-hover:text-black transition-colors" />
                </Link>
              </>
            ) : (
              <div className="flex-1 rounded-full border border-night-line px-5 py-3 text-xs text-zinc-500">
                {school.shortName} coming soon…
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Stats band — giant thin numerals over hairlines */}
      <div className="border-y border-night-line">
        <div className="max-w-[1400px] mx-auto px-6 py-12 md:py-16">
          {school.live ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-x-6 gap-y-10">
              {school.stats.map((s) => (
                <div key={s.label} className="flex flex-col gap-2">
                  <span className="font-[330] text-4xl md:text-5xl tabular-nums leading-none">{s.value}</span>
                  <span className="text-xs uppercase tracking-[0.72px] text-zinc-500">{s.label}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <span className="size-1.5 rounded-full bg-white" />
              <p className="text-sm text-zinc-400">
                <span className="text-white">{school.shortName}</span>&apos;s catalog is being indexed — join the waitlist to get notified first.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Closing CTA — one action, lots of air */}
      <section className="max-w-[1400px] w-full mx-auto px-6 py-28 md:py-40">
        <p className="text-xs uppercase tracking-[0.72px] text-zinc-400 mb-6">
          {school.live ? "Get started free" : "Be first to know"}
        </p>
        <h2 className="font-[330] leading-[1.05] text-[clamp(2.25rem,5.5vw,4.375rem)] text-balance max-w-4xl">
          {school.live
            ? "Your questions, answered instantly."
            : `${school.shortName} is next on the list.`}
        </h2>
        <p className="mt-6 text-lg leading-[1.56] text-zinc-400 max-w-xl">
          {school.live
            ? "No advisor queue. No calendar rabbit holes. Just ask."
            : `We're indexing ${school.shortName}'s catalog now. Join the waitlist and we'll email you the day it opens.`}
        </p>

        <div className="mt-10">
          {school.live ? (
            <Link
              href="/sign-up"
              className="inline-flex items-center gap-2 rounded-full border-2 border-white px-7 py-3 text-base text-white hover:bg-white hover:text-black transition-colors"
            >
              Open CampusQ free
              <ArrowRight className="size-4" />
            </Link>
          ) : (
            <WaitlistCta school={school.shortName} />
          )}
        </div>

        <p className="mt-7 text-xs text-zinc-500">
          Not affiliated with {school.name}
        </p>
      </section>

      {/* Footer — footer-dark with muted cool link tones */}
      <footer className="border-t border-night-line px-6 py-16 mt-auto">
        <div className="max-w-[1400px] mx-auto flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <span className="text-sm">
              <span className="font-[550]">Campus</span><span className="font-[330]">Q</span>
            </span>
            <span className="text-zinc-700">·</span>
            <a href="https://retriive.com" className="text-xs text-night-link underline underline-offset-2 hover:text-white transition-colors">
              by Retriive
            </a>
          </div>
          <div className="flex items-center gap-8 text-xs">
            <Link href="/chat" className="text-night-link underline underline-offset-2 hover:text-white transition-colors">App</Link>
            <Link href="/about" className="text-night-link underline underline-offset-2 hover:text-white transition-colors">About</Link>
            <a href="mailto:mahadmyonis@gmail.com" className="text-night-link underline underline-offset-2 hover:text-white transition-colors">Contact</a>
          </div>
        </div>
      </footer>

    </div>
  )
}
