# CampusQ Business Model

**Status:** Draft for team decision — owners Mahad & Abdulla (issue #100).
**Goal:** weigh our options, write the cost math down, and **get a decision on paper.**

> This is a working doc, not a final pricing sheet. Numbers marked _est._ are
> planning estimates and must be re-verified against live vendor pricing before
> we quote anyone. Where the code already answers a question, this doc cites it.

---

## 1. What we're actually selling

Two layers, one product (see [PITCH.md](PITCH.md)):

| Layer | Buyer | Willing to pay because… |
|---|---|---|
| **Answer layer** | Students (free) | It's better than the university's own search. Drives adoption; it is **not** the revenue line. |
| **Intelligence layer** | Advising / student-services staff | Weekly anonymized reports: top question clusters, content gaps, after-hours demand. This is why the **institution** pays. |

**Pricing principle:** students are always free; the **institution** pays for
the intelligence layer and the operational guarantees around it. Charging
students would kill the bottom-up adoption that creates our institutional
champion.

---

## 2. Unit economics — how to calculate cost

Costs split into three buckets. Only the first scales with usage.

### 2a. Marginal cost per answered question (variable)

Grounded in the current pipeline (`backend/main.py`, `backend/retrieval.py`):

| Step | What runs | Est. cost / question |
|---|---|---|
| Query rewrite (long queries only) | `gpt-4o-mini`, ≤80 tok out | ~$0.00002 |
| Query embedding | `text-embedding-3-small`, ~40 tok | ~$0.000001 |
| Vector search | Pinecone serverless read (top-k ≤30) | ~$0.0001 |
| Rerank | Cohere `rerank-english-v3.0` (skipped on strong scores; LLM fallback) | ~$0.002 |
| Answer generation | `gpt-4o-mini`, ~4–6k tok in + ~400 tok out | ~$0.0009 |
| **Total** | | **≈ $0.003 / answer** |

**Planning number: ~$0.005 per answered question** (rounds up for retries,
logging, embeddings, and occasional LLM rerank fallback).

> Formula: `variable_cost ≈ questions_per_month × $0.005`
> Example: 10,000 questions/mo ≈ **$50/mo**. 100,000 questions/mo ≈ **$500/mo**.

**Takeaway:** inference is cheap. Marginal cost is *not* the constraint — a
single institution license covers years of a campus's question volume. The cost
model that matters is the **fixed** bucket below, and the pricing model that
matters is packaging, not metering.

### 2b. Fixed platform cost (shared across all schools)

| Service | Plan | Est. / month |
|---|---|---|
| Vercel (frontend) | Pro | ~$20 |
| Render (backend) | Standard service(s) | ~$25–85 |
| Pinecone | Serverless (one `knowledge-base` index, per-school namespaces) | ~$0–70 |
| Clerk (auth) | Free < 10k MAU, then ~$25 + $0.02/MAU | ~$0–100 |
| **Subtotal** | | **~$70–275 / mo total** — _not per school_ |

Because we run **one shared index with per-school namespaces**
(`pc.Index("knowledge-base")` in `backend/main.py`), adding school #2 adds
almost nothing here — it's a data problem, not a build problem.

### 2c. Per-school onboarding cost (mostly labour)

Scraping + ingesting a new school's data (`backend/ingestion/`): mostly
engineering time + trivial compute. This is the real per-school cost. Track it
as **hours**, not dollars, and it drops each time we automate more of ingest.

### The one-line cost model

```
monthly_cost ≈ SHARED_PLATFORM (~$70–275)
             + Σ_schools (questions_per_school × $0.005)
             + amortized onboarding labour per school
```

Gross margin per institution is very high — the strategic question is **what to
charge**, not **how to cut cost**.

---

## 3. Deployment topology options (local vs external vs owner-tenant)

This is the "local instancing vs externally instanced product" question, plus
Abody's Azure owner-tenant idea.

| Option | What it means | Cost to us | Unlocks | Verdict |
|---|---|---|---|---|
| **A. Shared multi-tenant** (current) | One backend + one Pinecone index, per-school namespaces | Lowest | Fast school onboarding, high margin | **Default for most schools** |
| **B. Dedicated single-tenant** | Separate deployment per school (isolated DB/instance) | Medium (ops per school) | Data-isolation requirements, custom SLAs | Only when procurement/security demands it |
| **C. Owner-tenant (Azure)** | CampusQ runs **inside the university's own cloud tenant**; their data never leaves their environment | Highest (a real port) | Security-strict buyers, data-residency, premium price | **Premium enterprise tier only** |

**Note on Option C:** our stack today is OpenAI + Pinecone + Vercel + Render. A
true owner-tenant Azure deploy means Azure OpenAI + Azure AI Search (or
self-hosted vectors) + container hosting — a genuine engineering port. Price it
as a premium add-on, not the default, and only build it against a signed deal.
(Tracked under issue #100 → Abody's Azure spike.)

**Recommendation:** default everyone to **A**, keep **C** as the top pricing
tier we *offer* but only *build* when a paying enterprise/consortium requires
it.

---

## 4. Pricing model options

| Model | Pros | Cons | Fit |
|---|---|---|---|
| Per-institution annual license (flat) | Simple, budget-friendly for higher-ed procurement | Leaves value on the table for big schools | ✅ Core |
| **Tiered** (size + features) | Captures big vs small schools; upsell path | Need clean tier boundaries | ✅ **Recommended** |
| Per-seat (per student MAU) | Scales with usage | Unpredictable budget → procurement hates it | ❌ Avoid |
| Pure usage (per question) | Aligns to cost | Same budget-unpredictability problem; cost is tiny anyway | ❌ Avoid |
| Freemium (students free, institution pays) | Matches our adoption motion | — | ✅ Already our frame |

**Chosen frame:** annual **institutional SaaS license, tiered**, students always
free. Tiers gate *features and deployment*, not student headcount.

### Proposed tiers (the X / Y / Z idea)

> Dollar figures are placeholders for the team to set — anchors in §5.

| Tier | Who | Includes | Price |
|---|---|---|---|
| **1 — Essentials (X)** | Small college / single faculty | Answer layer + basic dashboard | $X / yr |
| **2 — Intelligence (Y)** | Mid/large university | + weekly advisor reports, gap analysis, after-hours analytics, multi-department | $Y / yr |
| **3 — Enterprise / Sovereign (Z)** | Security-sensitive / large institutions | + dedicated or **owner-tenant (Azure)** deploy, SSO, SLA, data residency | $Z / yr |
| **Consortium** | Ontario system / U15 | Multi-campus, one relationship | Custom |

Tier 2 is the product we lead with — it's where the intelligence-layer moat
lives. Tier 3 is where owner-tenant (§3C) is sold.

---

## 5. Reference point: Brightspace / D2L

D2L sells **institution-wide annual licenses** (LMS), typically five-to-six
figures/year depending on enrolment, sold through slow committee procurement.
Lessons for us:

- **Institution-wide annual license is the norm** buyers expect → validates §4.
- Their weakness is **procurement speed**; our bottom-up student adoption +
  advisor-report champion routes around it (see [PITCH.md](PITCH.md) §Distribution).
- We are a **point solution**, not an LMS. Ed-tech point tools commonly land in
  the **~$10k–$60k/institution/year** _est._ range — a reasonable starting
  anchor for Tiers 1–2, with Tier 3/consortium above it. **Re-verify with real
  comparables before quoting.**

---

## 6. Recommendation (the decision to put on paper)

1. **Students free, institution pays.** Never charge students.
2. **Externally instanced (multi-tenant, Option A) is the default.** It's what
   the code already does and it keeps margins high.
3. **Pricing = annual institutional license, tiered** (Essentials / Intelligence
   / Enterprise-Sovereign + Consortium). Tiers gate features + deployment, not
   student count.
4. **Owner-tenant Azure (Option C) = Tier 3 only**, built against a signed deal,
   not speculatively.
5. **Free-AI viability:** given ~$0.005/question, self-hosting a free model to
   save inference cost is **not worth it yet** — the savings are noise against
   fixed + labour costs, and quality/eval risk is real. Revisit only at large
   scale. (Feeds issue #103.)

### Open decisions for the team

- [ ] Set actual $ for X / Y / Z (§4) — needs 2–3 real comparables.
- [ ] Confirm provincial vs federal incorporation affects contracting (issue #99).
- [ ] Confirm the model against Islamic-finance guidance on investment/shares
      (issue #101) before finalizing terms.
- [ ] Abody's Azure owner-tenant feasibility spike (issue #100) → informs Tier 3 cost.

---

_Source: team meeting action items (issue #100). Cost figures derived from
`backend/main.py`, `backend/retrieval.py`, `backend/guest_quota.py` and current
vendor pricing as of 2026 — re-verify before quoting._
