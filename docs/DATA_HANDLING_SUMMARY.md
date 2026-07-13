# CampusQ Data Handling Summary

**One-page overview for university partners (e.g. Carleton).**  
Last updated: July 2026 · Operator: Retriive · Product: CampusQ

---

## What CampusQ is

CampusQ is an independent AI academic assistant. It is **not** affiliated with, endorsed by, or operated by any university. Answers are generated from publicly available university sources (calendars, catalogs, regulations) plus student-submitted questions.

---

## What we log (server-side)

| Data | Purpose | Identifiers |
|------|---------|-------------|
| Chat questions (truncated to 300 chars) | Quality monitoring, gap detection, advisor reports | Pseudonymized user ID (HMAC hash — not raw Clerk ID) |
| Retrieval stats (scores, namespaces) | Improve search and data coverage | Same pseudonymized ID |
| Thumbs up/down + optional feedback | Measure helpfulness | Session ID + truncated Q/A |
| “Report a problem” submissions | Support and quality fixes | Session ID + truncated Q/A |
| Waitlist email + school | Notify when a school launches | Email (with explicit consent) |
| Calendar feed fetches | Usage proof for deadline feature | Anonymous |
| Synced chat history (signed-in users only) | Cross-device chat restore for accounts | Clerk user id (account store, not public logs) |

**Guests:** chat history stays on-device only (`localStorage`).  
**Signed-in students:** recent chat sessions are also stored in our account sync database so history follows them across devices.

---

## Retention

- **Server logs:** automatically deleted after **90 days** (`LOG_RETENTION_DAYS`, default 90).
- **Browser chat history:** until the student deletes chats or clears site data.
- **Synced account chat history:** until the student deletes chats in-app or requests account deletion.
- **Waitlist emails:** until the student unsubscribes or requests deletion.

---

## Who can see what

| Audience | Access |
|----------|--------|
| **Students** | Their own chats on their device; sign-in via Clerk |
| **Retriive engineering** | Internal admin dashboard (protected by admin API key + planned Clerk roles) — raw log files on Render persistent disk |
| **University staff (advisor reports)** | **Aggregated** question trends, intents, departments, gap themes — **no student names, emails, or Clerk IDs** |
| **Subprocessors** | See “Vendors” below — process data under their own terms |

Advisor reports are designed for “what are students asking about?” — not individual tracking.

---

## Deletion requests

Students or waitlist signups can email **hello@retriive.com** and request deletion of server-side records tied to their email or account.

**We will:**
1. Confirm the requester’s identity (email match or Clerk account).
2. Remove matching waitlist entries and pseudonymized log lines where feasible within **30 days**.
3. Confirm completion by email.

**Note:** Browser-local chat history must be cleared by the student on their device; we cannot remote-delete `localStorage`.

---

## Vendors (subprocessors)

| Vendor | Role | Data they may process |
|--------|------|------------------------|
| **OpenAI** | Language model inference | Question text, retrieved context, generated answers |
| **Pinecone** | Vector search | Embeddings of public university content + query embeddings |
| **Cohere** | Reranking (optional) | Query + candidate text snippets |
| **Clerk** | Authentication | Email, profile, session tokens |
| **Vercel** | Frontend hosting + analytics | Page views, anonymous event categories (not full question text) |
| **Render** | Backend API hosting | API requests, log files on persistent disk |
| **Resend** | Email delivery | Recipient addresses for waitlist/ops emails |
| **Sentry** | Error monitoring (when enabled) | Error stack traces, request metadata — no intentional PII |

A formal Data Processing Agreement (DPA) can be provided on request for institutional pilots.

---

## Security controls (summary)

- Pseudonymized user IDs in all server logs  
- Rate limiting on chat, waitlist, and feedback endpoints  
- Admin routes default-closed without `ADMIN_API_KEY`  
- Optional Clerk JWT enforcement (`REQUIRE_AUTH`) for production  
- 90-day automated log pruning  

---

## Contact

**Privacy / data requests:** hello@retriive.com  
**Technical / pilot questions:** hello@retriive.com

For a full student-facing policy, see the in-app [Privacy Policy](https://try-campusq.vercel.app/privacy).
