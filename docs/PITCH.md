# How We Pitch CampusQ

The positioning we use everywhere — deck, website, demo day, cold emails. One
story, told consistently. If you're writing anything external-facing, start here.

> **Status:** This replaces the old "RAG with citations / no hallucinations"
> framing. Do not use that framing anymore — it describes our mechanism, and
> the mechanism is table stakes. This doc describes our *position*.

---

## The one-liner

> **CampusQ answers students' questions from official university data — and
> turns every question into intelligence the university can't get anywhere
> else.**

Two layers, one product:

| Layer | Who it serves | What it does |
|---|---|---|
| **Answer layer** | Students | Accurate answers about courses, programs, deadlines, registration — grounded in official data, with sources |
| **Intelligence layer** | Advising & student services staff | Anonymized weekly reports: what students are asking, where the university's own content has gaps, how much demand happens after hours |

The answer layer is what students see. The intelligence layer is why the
institution pays, why we're hard to rip out, and why we get harder to copy
every week we're live.

---

## Why we win (the actual differentiators)

### 1. We don't use AI when we don't have to

Every competitor pitches "AI search with citations." We route *away* from the
LLM whenever data is structured: Program Explorer, the deadline tracker, and
course lookup are deterministic — no model, no chance of being wrong. Chat
handles only what genuinely needs language understanding, and every deploy is
gated by an automated quality suite ([QUALITY_GATE.md](QUALITY_GATE.md)).

**Say it this way:** "Our accuracy story isn't a better prompt — it's an
architecture that only uses AI where AI is necessary."

### 2. The question-gap data asset (our moat)

Every question a student asks — including the ones we *can't* answer — is
logged, clustered, and anonymized (`backend/dashboard.py`,
`backend/advisor_report.py`). Over time this becomes a map of what students
at each institution actually need to know, where the official content fails
them, and how demand moves across the academic year.

An LMS vendor can ship "cite your handbook" as a feature next quarter. They
cannot ship a year of Carleton-specific question-and-gap data. Our moat isn't
the retrieval pipeline — it's the demand-side dataset the pipeline generates,
which compounds with usage and doesn't exist anywhere else, not even inside
the university.

### 3. Embedded in staff workflow, not bolted onto a website

The weekly advisor report goes in front of advising and student services staff
and is framed around *their* job: top question clusters, content gaps to fix,
after-hours volume for staffing decisions. A search bar is one procurement
cycle from being replaced; a report that staff use to run their office is not.

This is also our buyer story: the report creates an internal champion in the
advising office — someone whose work measurably improves because of us —
instead of leaving us at the mercy of a slow procurement committee.

---

## Beachhead → platform (the map)

**Beachhead:** university academic advising — dense, exception-riddled policy
(calendars, regulations, registrar rules, deadlines) plus a high-volume
audience that asks the same hard questions every term.

**Platform:** the institutional answer layer for any organization whose
knowledge lives in policy documents full of exceptions — starting with the
rest of higher ed, with the same engine applicable to any policy-dense
institution.

**The expansion proof is engineering, not narrative:** our ingest pipeline
(`backend/ingest/`, `backend/run_pipeline.py`, per-category Pinecone
namespaces) makes onboarding a new institution a *data* problem, not a
*build* problem. School #2 at near-zero marginal engineering cost is the
slide. Don't claim hospitals and governments before we've proven the second
campus — a stated map with a proven first hop beats a grand vision with no
hops.

---

## Distribution (not school-by-school enterprise sales)

The critique of higher ed — committee purchasing, 6–12 month cycles — is real
if you sell top-down only. Our model routes around it:

1. **Bottom-up student adoption first.** Students use CampusQ because it's
   better than the university's own search. Live at Carleton (beta); waitlist
   landing pages already up for uOttawa, UofT, Waterloo, Western. Waitlist
   counts are demand evidence the procurement committee didn't ask for and
   can't ignore.
2. **The advisor report converts usage into an institutional buyer.** Staff
   see the gap report, staff want the gap report, staff become the champion.
3. **System-level multipliers.** Ontario universities / U15 as consortium
   channels: one relationship, many campuses. This is the land-and-expand
   *across* institutions story.

---

## Founder-market fit

**Be honest here — an honest gap beats an invisible one.**

<!-- TEAM: fill this in truthfully. If someone has worked in a registrar's
office, university IT, student government, or sold into higher ed, lead with
it. Lived experience as students *at the target school* counts — "we built
this because Carleton's own tools failed us" is a real insider story — but
name the gap on the institutional-sales side and say who (advisor, early
hire) fills it. -->

- Insider knowledge we have: **[fill in]**
- The gap: **[fill in — e.g. "none of us has sold into university
  administration"]**
- How we're closing it: **[fill in — e.g. named advisor with registrar /
  ed-tech sales background]**

---

## Proof points to collect (before the next pitch)

One real number beats any narrative. Highest-leverage first:

- [ ] **Advisor-report adoption at Carleton** — is advising staff receiving
      and acting on the weekly report? Get a quote or a "they asked for X"
      moment.
- [ ] **After-hours demand %** — from the dashboard. "X% of student questions
      arrive when no human is available" is the urgency stat.
- [ ] **Coverage-gap count** — "we surfaced N questions Carleton's own
      website couldn't answer" proves the intelligence layer with one number.
- [ ] **Waitlist counts** at uOttawa / UofT / Waterloo / Western — demand
      evidence for the expansion story.
- [ ] **Retention / repeat usage** at Carleton — proves students come back,
      not just try it once.

---

## Deck outline (10 slides)

1. **Problem** — students get wrong answers about the rules that govern their
   degree; universities have no visibility into what students can't find.
2. **Product** — the answer layer (live demo: Program Explorer + chat).
3. **The intelligence layer** — show a real (anonymized) advisor report. This
   is the slide that separates us from every "AI search" pitch.
4. **Why we're accurate** — deterministic-first architecture + quality gate.
5. **Moat** — the question-gap dataset compounds with usage; competitors can
   scrape the PDFs, not the demand.
6. **Traction** — Carleton live; proof points from the checklist above.
7. **Distribution** — bottom-up students → advisor champion → system-level
   deals. Waitlist schools as the next wave.
8. **Market map** — advising beachhead → higher-ed platform → policy-dense
   institutions.
9. **Team** — founder-market fit, honestly stated (see above).
10. **Ask.**

---

## What we stopped saying (and why)

| Old framing | Why it's retired |
|---|---|
| "RAG with citations" | Mechanism, not position. Every vertical AI search startup says it. |
| "Eliminates hallucinations" | Minimum bar, not a differentiator — and our real accuracy story (deterministic-first) is stronger. |
| Higher ed as the whole story | It's the beachhead. Say where the map leads. |
| Search bar as the product | The product is answers *plus* institutional intelligence. The report is first-class, not a side script. |
