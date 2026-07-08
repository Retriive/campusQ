import { Metadata } from "next"
import Link from "next/link"
import { ArrowRight, ShieldCheck, Mail } from "lucide-react"

export const metadata: Metadata = {
  title: "About — CampusQ",
  description: "CampusQ is an AI academic assistant for Canadian university students.",
}

// Dots use each school's own accent token theme (see [data-school] in globals.css)
const SCHOOLS_STATUS = [
  { name: "Carleton University", short: "Carleton", status: "live" as const, school: "carleton" },
  { name: "University of Ottawa", short: "uOttawa", status: "soon" as const, school: "uottawa" },
  { name: "University of Toronto", short: "UofT", status: "soon" as const, school: "uoft" },
  { name: "University of Waterloo", short: "Waterloo", status: "soon" as const, school: "waterloo" },
  { name: "Western University", short: "Western", status: "soon" as const, school: "western" },
]

export default function AboutPage() {
  return (
    <div data-school="carleton" className="min-h-screen bg-background text-foreground flex flex-col">

      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-border/60 bg-card/80 backdrop-blur-2xl">
        <div className="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">
          <Link href="/" className="text-sm font-bold tracking-tight">
            Campus<span className="text-primary">Q</span>
          </Link>
          <Link
            href="/chat"
            className="inline-flex items-center gap-1.5 bg-primary text-primary-foreground text-xs font-semibold px-4 py-2 rounded-lg hover:bg-primary-strong transition-colors shadow-resting"
          >
            Open app <ArrowRight className="size-3" />
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden border-b border-border/60">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_70%_60%_at_50%_-10%,var(--primary-soft),transparent)]" />
        <div className="absolute inset-0 opacity-[0.03]"
          style={{ backgroundImage: "radial-gradient(circle, currentColor 1px, transparent 1px)", backgroundSize: "24px 24px" }} />
        <div className="relative max-w-5xl mx-auto px-6 py-20 md:py-28">
          <p className="text-xs font-semibold text-muted-foreground/80 uppercase tracking-widest mb-5">About CampusQ</p>
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-foreground max-w-2xl mb-6 text-balance">
            Academic questions,<br />
            <span className="text-primary">answered instantly.</span>
          </h1>
          <p className="text-muted-foreground text-base max-w-lg">
            CampusQ is an independent AI assistant built for Canadian university students. Ask anything
            about courses, prerequisites, programs, or deadlines — get a real answer in seconds, sourced
            directly from official university documents.
          </p>
        </div>
      </section>

      <main className="max-w-5xl mx-auto px-6 py-16 w-full flex flex-col gap-20">

        {/* Why */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-10 items-start">
          <div>
            <p className="text-xs font-semibold text-muted-foreground/80 uppercase tracking-widest mb-5">Why we built it</p>
            <h2 className="text-2xl md:text-3xl font-bold text-foreground tracking-tight">
              The information exists.<br />It's just inaccessible.
            </h2>
          </div>
          <div className="flex flex-col gap-5 text-base text-muted-foreground">
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
              We're rolling out to every major Canadian university. Same idea, every campus.
            </p>
          </div>
        </section>

        {/* Schools */}
        <section>
          <p className="text-xs font-semibold text-muted-foreground/80 uppercase tracking-widest mb-8">Where we're at</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {SCHOOLS_STATUS.map((s) => (
              <div
                key={s.name}
                data-school={s.school}
                className={`relative rounded-2xl border p-5 flex flex-col gap-3 overflow-hidden transition-all ${
                  s.status === "live"
                    ? "border-border bg-card shadow-resting"
                    : "border-border/60 bg-secondary/50"
                }`}
              >
                {/* color dot — takes this school's accent token */}
                <div className="size-2 rounded-full bg-primary" />
                <div>
                  <p className={`text-sm font-semibold ${s.status === "live" ? "text-foreground" : "text-muted-foreground"}`}>
                    {s.name}
                  </p>
                </div>
                <div className="mt-auto">
                  {s.status === "live" ? (
                    <span className="inline-flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wide text-success bg-success/10 border border-success/25 px-2.5 py-1 rounded-lg">
                      <span className="size-1.5 rounded-full bg-success" />
                      Live
                    </span>
                  ) : (
                    <span className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground/80">
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
            <p className="text-xs font-semibold text-muted-foreground/80 uppercase tracking-widest mb-5">The company behind it</p>
            <h2 className="text-2xl md:text-3xl font-bold text-foreground tracking-tight">
              CampusQ is built by <span className="text-primary">Retriive</span>.
            </h2>
          </div>
          <div className="flex flex-col gap-5 text-base text-muted-foreground">
            <p>
              Retriive builds AI solutions for institutions and enterprises — systems that
              <span className="text-secondary-foreground font-medium"> eliminate informational silos</span> and
              <span className="text-secondary-foreground font-medium"> optimize administrative efficiency</span> across
              an organization.
            </p>
            <p>
              The problem is the same everywhere: the answer already exists, but it's buried across PDFs,
              portals, inboxes, and people's heads — so the person who needs it can't find it. Retriive
              unifies that scattered knowledge and puts a precise, source-grounded answer one question away.
            </p>
            <p>
              CampusQ is that idea applied to universities — the first of many domains where Retriive turns
              fragmented information into instant, trustworthy answers.
            </p>
          </div>
        </section>

        {/* Disclaimer + Contact side by side */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="rounded-2xl border border-border/60 bg-secondary/50 p-6 flex flex-col gap-3">
            <div className="flex items-center gap-2.5">
              <ShieldCheck className="size-4 text-muted-foreground shrink-0" />
              <span className="text-sm font-semibold text-foreground">Heads up</span>
            </div>
            <p className="text-sm text-muted-foreground">
              CampusQ is an <span className="text-secondary-foreground font-medium">independent tool</span> — not
              affiliated with, endorsed by, or operated by any university. Always verify important
              academic decisions with your advisor or official university sources.
            </p>
          </div>

          <div className="rounded-2xl border border-border/60 bg-secondary/50 p-6 flex flex-col gap-3">
            <div className="flex items-center gap-2.5">
              <Mail className="size-4 text-muted-foreground shrink-0" />
              <span className="text-sm font-semibold text-foreground">Get in touch</span>
            </div>
            <p className="text-sm text-muted-foreground">
              Found an error, have feedback, or want to bring CampusQ to your school?
            </p>
            <a
              href="mailto:team@retriive.com"
              className="mt-auto inline-flex items-center gap-1.5 text-sm font-medium text-secondary-foreground hover:text-foreground transition-colors"
            >
              mahadmyonis@gmail.com <ArrowRight className="size-3.5" />
            </a>
          </div>
        </section>

      </main>

      {/* Footer */}
      <footer className="border-t border-border/60 px-6 py-6 mt-auto">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Link href="/" className="text-sm font-bold">
              Campus<span className="text-primary">Q</span>
            </Link>
            <span className="text-border">·</span>
            <a href="https://retriive.com" className="text-xs text-muted-foreground hover:text-foreground transition-colors">
              by Retriive
            </a>
          </div>
          <span className="text-xs text-muted-foreground">Not affiliated with any university</span>
        </div>
      </footer>

    </div>
  )
}
