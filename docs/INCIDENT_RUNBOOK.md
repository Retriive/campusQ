# Incident Runbook

How CampusQ responds when something breaks in production.

---

## On-call ownership

| Role | Owner | Contact |
|------|-------|---------|
| **Incident lead** | Whoever is shipping that week | Team Slack `#incidents` |
| **Backend / API** | Backend dev on rotation | See team roster |
| **Frontend** | Frontend dev on rotation | See team roster |
| **Comms (university-facing)** | Mahad | hello@retriive.com |

---

## Severity levels

| Level | Definition | Examples | Target response |
|-------|------------|----------|-----------------|
| **SEV-1** | Chat completely down or data leak suspected | 500s on all chat requests, auth bypass, log exposure | Immediate — all hands |
| **SEV-2** | Major feature degraded | Retrieval failing, stream timeouts, dashboard down | < 1 hour |
| **SEV-3** | Partial degradation | Slow answers, one tool broken, single scraper stale | < 4 hours |
| **SEV-4** | Minor / cosmetic | UI glitch, non-critical log noise | Next business day |

---

## How we know something is wrong

| Signal | Where |
|--------|-------|
| **Smoke gate failed** | GitHub Actions → Slack alert (if `SLACK_WEBHOOK_URL` configured) |
| **Uptime monitor** | External monitor on `GET /health/ready` (configure in Better Uptime, UptimeRobot, or similar) |
| **Sentry errors** | Sentry dashboard — 5xx spikes, unhandled exceptions |
| **User reports** | “Report a Problem” in app, email, Slack |
| **Render alerts** | Render dashboard — deploy failures, instance restarts |

### Health endpoints

| Endpoint | Use |
|----------|-----|
| `GET /` | Shallow liveness — process is up |
| `GET /health/ready` | Deep readiness — Pinecone + OpenAI connectivity. **Point uptime monitors here.** |

Expected ready response: `200` with `"status": "ready"`.  
Degraded: `503` with per-check errors in `checks`.

---

## First 15 minutes (any SEV-1 / SEV-2)

1. **Acknowledge** in `#incidents` — state severity and symptoms.
2. **Check health:** `curl https://<API_URL>/health/ready`
3. **Check Sentry** for new error groups in the last hour.
4. **Check Render** — last deploy, instance status, env vars.
5. **Run smoke gate** against production:
   ```bash
   cd backend
   CAMPUSQ_API_URL=https://<prod-api> OPENAI_API_KEY=... python evals/quality_gate.py --tier smoke
   ```
6. **Decide:** rollback vs hotfix (see below).

---

## Rollback steps

### Backend (Render)

1. Render dashboard → campusQ API service → **Deploys**
2. Select last known-good deploy → **Rollback**
3. Verify: `curl /health/ready` + smoke gate 10/10

### Frontend (Vercel)

1. Vercel dashboard → Deployments
2. Promote previous production deployment
3. Hard-refresh `/chat` and ask one smoke question manually

### Data (Pinecone)

- **Do not run `wipe.py`** during an incident unless explicitly recovering from bad index data.
- Re-index procedure: see `docs/PROJECT_MAP.md` → scrapers / ingest pipeline.

---

## Common incidents

### Chat returns errors / timeouts

1. Check `/health/ready` — which check failed?
2. **OpenAI down:** status.openai.com — enable status page comms if prolonged.
3. **Pinecone down:** status.pinecone.io
4. Check Render logs for rate limits or OOM.
5. Roll back if tied to recent deploy.

### Smoke gate failed on merge to main

1. Open GitHub Actions run → read experiment artifact.
2. Slack alert should fire automatically (if webhook configured).
3. **Do not deploy** until smoke passes on production URL.
4. If prod already deployed: rollback backend to last green deploy.

### Wrong answers (quality, not outage)

- **Not an infra incident** — follow `docs/TEAM_RULES.md` Rule 3.
- Check `queries.log` / `no_context.log` on Render disk.
- Run core gate; freeze features if below 80%.

### Suspected data / privacy issue

1. **SEV-1** — page incident lead + Mahad immediately.
2. Preserve logs (do not prune).
3. Identify scope: which endpoint, which logs, time window.
4. Rotate `ADMIN_API_KEY`, `USER_ID_HASH_SALT` if log integrity compromised.
5. Document timeline for partner notification if student data involved.

---

## Communication templates

### Internal (Slack `#incidents`)

```
[SEV-X] CampusQ — <one-line symptom>
Impact: <who is affected>
Status: investigating | identified | mitigating | resolved
Lead: @name
Next update: <time>
```

### University partner (if pilot is affected)

```
Subject: CampusQ service update

We are aware of an issue affecting CampusQ response times / availability.
Our team is actively working on a fix. We will send an update within <timeframe>.

CampusQ remains an independent tool — students should continue to verify
critical academic decisions with official university sources.

— Retriive / CampusQ team
```

---

## Post-incident

Within 48 hours of SEV-1/SEV-2 resolution:

1. Short postmortem in `docs/incidents/YYYY-MM-DD-<title>.md` (create folder as needed)
2. Include: timeline, root cause, fix, prevention action items
3. Link any new monitoring or tests added

---

## Environment variables for observability

| Variable | Service | Purpose |
|----------|---------|---------|
| `SENTRY_DSN` | Backend (Render) | Error tracking |
| `SENTRY_ENVIRONMENT` | Backend | `production` / `staging` |
| `NEXT_PUBLIC_SENTRY_DSN` | Frontend (Vercel) | Client + server error tracking |
| `SLACK_WEBHOOK_URL` | GitHub Actions secret | Smoke gate failure alerts |

### Uptime monitor setup (one-time)

1. Create account on Better Uptime, UptimeRobot, or similar.
2. Monitor URL: `https://<your-render-api>/health/ready`
3. Interval: 1–5 minutes
4. Alert channels: email + Slack
5. Document monitor URL in team Slack pinned message

---

## Related docs

- [Team Rules](TEAM_RULES.md) — deploy gates
- [Quality Gate](QUALITY_GATE.md) — smoke / core tests
- [Data Handling Summary](DATA_HANDLING_SUMMARY.md) — privacy posture for partners
- [Project Map](PROJECT_MAP.md) — where logs and code live
