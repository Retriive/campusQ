#!/usr/bin/env bash
# Generate a shared quality-gate secret and print the one-time setup commands.
set -euo pipefail

KEY="$(openssl rand -hex 32)"

cat <<EOF
CampusQ quality gate — one-time secret setup
============================================

Generated QUALITY_GATE_KEY:
  ${KEY}

1) GitHub Actions (repo → Settings → Secrets → Actions):
   Name:  QUALITY_GATE_KEY
   Value: ${KEY}

   Or via CLI (requires admin):
   gh secret set QUALITY_GATE_KEY --body "${KEY}"

2) Render (campusQ API service → Environment):
   Name:  QUALITY_GATE_KEY
   Value: ${KEY}

   Redeploy the backend after saving.

3) Optional — Clerk auto-mint instead (either works):
   gh secret set CLERK_SECRET_KEY --body "sk_test_..."

4) Re-run smoke gate:
   GitHub → Actions → Smoke quality gate → Run workflow

EOF
