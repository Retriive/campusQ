# CampusQ Frontend

Next.js web app for CampusQ — chat UI, landing pages, and admin tools.

**New to the project?** Start at the [main README](../README.md) and [Getting Started](../docs/GETTING_STARTED.md).

---

## What this folder does

| Path | Purpose |
|------|---------|
| `app/page.tsx` | Carleton landing page |
| `app/chat/page.tsx` | Main chat (beta product) |
| `app/dashboard/page.tsx` | Advisor analytics |
| `components/campus-q/` | Chat UI, program explorer, tools |
| `components/campus-q/chat/` | Chat-specific subcomponents + suggestion utilities |
| `components/landing/` | Multi-university waitlist pages |
| `lib/api.ts` | Canonical API base URL + fetch helper |

---

## Run locally

**Terminal 1 — Backend** (required):

```powershell
cd backend
py -m uvicorn main:app --reload --port 8000
```

**Terminal 2 — Frontend:**

```powershell
cd frontend
npm install
npm run dev
```

Open: http://localhost:3000

---

## Environment

Create `frontend/.env.local` (optional — defaults work for local dev):

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

If not set, the app talks to `http://localhost:8000` automatically.

---

## Pages

| URL | What it is |
|-----|------------|
| `/` | Carleton landing page |
| `/chat` | Main chat (beta) |
| `/dashboard` | Advisor analytics |
| `/about` | About page |

---

## Build for production

```powershell
npm run build
npm start
```

Production is deployed separately (e.g. Vercel for frontend, Render for backend).

---

## Tech stack

- **Next.js 14** (App Router)
- **React**
- **Tailwind CSS**
- **TypeScript**
