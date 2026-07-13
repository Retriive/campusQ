#!/usr/bin/env python3
"""
CampusQ Quality Gate — automated pass/fail check before deploy or expansion.

Runs golden questions against the live /api/chat/stream endpoint, applies
deterministic checks, then LLM-judges each answer against grading notes.

Usage:
  cd backend
  uvicorn main:app --reload          # in another terminal
  python evals/quality_gate.py --tier smoke
  python evals/quality_gate.py --tier core
  python evals/quality_gate.py --tier full

Exit codes:
  0 = gate passed
  1 = gate failed
  2 = setup error (API unreachable, missing keys)
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

EVALS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = EVALS_DIR.parent
DATASET_PATH = EVALS_DIR / "datasets" / "golden.csv"
EXPERIMENTS_DIR = EVALS_DIR / "experiments"

API_URL = os.getenv("CAMPUSQ_API_URL", "http://localhost:8000")
JUDGE_MODEL = os.getenv("CAMPUSQ_JUDGE_MODEL", "gpt-4o-mini")


def _clerk_token() -> str:
    return os.getenv("CAMPUSQ_CLERK_TOKEN", "").strip()


def chat_auth_headers() -> dict[str, str]:
    token = _clerk_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def ensure_chat_auth(api_url: str) -> None:
    """Fail fast when production requires Clerk auth but no token is configured."""
    if _clerk_token():
        return
    if "localhost" in api_url or "127.0.0.1" in api_url:
        return
    resp = None
    try:
        resp = requests.post(
            f"{api_url}/api/chat/stream",
            data={
                "question": "ping",
                "history": "[]",
                "session_id": "quality-gate-probe",
                "user_id": "quality-gate",
            },
            timeout=30,
            stream=True,
        )
        if resp.status_code == 401:
            print("ERROR: API requires Clerk auth (401 on /api/chat/stream).")
            print("Set CAMPUSQ_CLERK_TOKEN to a valid Clerk session JWT.")
            print("For CI: add CAMPUSQ_CLERK_TOKEN to GitHub Actions secrets.")
            sys.exit(2)
    except requests.RequestException:
        pass
    finally:
        if resp is not None:
            resp.close()

# ── Official Retriive quality gate thresholds ────────────────────────────────
GATE_THRESHOLDS = {
    "smoke": {"min_pass_rate": 1.00, "label": "Deploy gate — block production deploy if any smoke test fails"},
    "core": {"min_pass_rate": 0.85, "label": "Expansion gate — block new school / public launch below 85%"},
    "full": {"min_pass_rate": 0.80, "label": "Regression floor — track quality; investigate below 80%"},
}


@dataclass
class GoldenRow:
    tier: str
    id: str
    category: str
    question: str
    grading_notes: str
    must_contain: list[str] = field(default_factory=list)
    must_contain_any: list[str] = field(default_factory=list)
    must_not_contain: list[str] = field(default_factory=list)
    require_no_sources: bool = False


@dataclass
class EvalResult:
    row: GoldenRow
    answer: str
    sources: list[dict]
    passed: bool
    reason: str
    checks: list[str] = field(default_factory=list)


def load_golden_rows() -> list[GoldenRow]:
    rows: list[GoldenRow] = []
    with open(DATASET_PATH, encoding="utf-8") as f:
        for raw in csv.DictReader(f):
            rows.append(GoldenRow(
                tier=raw["tier"].strip(),
                id=raw["id"].strip(),
                category=raw["category"].strip(),
                question=raw["question"].strip(),
                grading_notes=raw["grading_notes"].strip(),
                must_contain=[p.strip() for p in raw.get("must_contain", "").split("|") if p.strip()],
                must_contain_any=[p.strip() for p in raw.get("must_contain_any", "").split("|") if p.strip()],
                must_not_contain=[p.strip() for p in raw.get("must_not_contain", "").split("|") if p.strip()],
                require_no_sources=raw.get("require_no_sources", "").strip().lower() in ("yes", "true", "1"),
            ))
    return rows


def rows_for_tier(rows: list[GoldenRow], tier: str) -> list[GoldenRow]:
    if tier == "smoke":
        return [r for r in rows if r.tier == "smoke"]
    if tier == "core":
        return [r for r in rows if r.tier in ("smoke", "core")]
    if tier == "full":
        return rows
    raise ValueError(f"Unknown tier: {tier}")


def ask_stream(question: str, api_url: str) -> tuple[str, list[dict]]:
    answer = ""
    sources: list[dict] = []
    resp = requests.post(
        f"{api_url}/api/chat/stream",
        data={"question": question, "history": "[]", "session_id": "quality-gate", "user_id": "quality-gate"},
        headers=chat_auth_headers(),
        stream=True,
        timeout=120,
    )
    resp.raise_for_status()
    for raw in resp.iter_lines(decode_unicode=True):
        if not raw or not raw.startswith("data: "):
            continue
        try:
            parsed = json.loads(raw[6:])
        except json.JSONDecodeError:
            continue
        if parsed.get("type") == "token":
            answer += parsed.get("content", "")
        elif parsed.get("type") == "sources":
            sources = parsed.get("data", [])
    return answer.strip(), sources


def run_deterministic_checks(row: GoldenRow, answer: str, sources: list[dict]) -> tuple[bool, list[str]]:
    notes: list[str] = []
    lower = answer.lower()

    if row.require_no_sources and sources:
        notes.append(f"FAIL: expected no sources, got {len(sources)}")
        return False, notes

    for phrase in row.must_contain:
        if phrase.lower() not in lower:
            notes.append(f"FAIL: missing required phrase '{phrase}'")
            return False, notes

    if row.must_contain_any and not any(p.lower() in lower for p in row.must_contain_any):
        notes.append(f"FAIL: none of required phrases found ({', '.join(row.must_contain_any)})")
        return False, notes

    for phrase in row.must_not_contain:
        if phrase.lower() in lower:
            notes.append(f"FAIL: forbidden phrase in answer '{phrase}'")
            return False, notes
        for src in sources:
            blob = f"{src.get('title', '')} {src.get('section', '')}".lower()
            if phrase.lower() in blob:
                notes.append(f"FAIL: forbidden phrase in sources '{phrase}'")
                return False, notes

    if not notes:
        notes.append("deterministic checks passed")
    return True, notes


def llm_judge(client: OpenAI, row: GoldenRow, answer: str) -> tuple[bool, str]:
    if answer.startswith("[REQUEST ERROR"):
        return False, "request to chat API failed"

    prompt = f"""You are grading CampusQ, an AI assistant for Carleton University students.

Question: {row.question}

AI Response:
{answer}

Grading notes (what a correct answer must satisfy):
{row.grading_notes}

Rules:
- Return pass only if the response satisfies the grading notes.
- Be strict on wrong dates, wrong prerequisites, invented courses, and actionable misinformation.
- For "should ask which program" cases, pass only if it asks for program clarification.
- For "must decline" cases, pass only if it appropriately refuses.
- Partial or vague answers that miss required facts = fail.
- Different wording is fine if the facts are correct.

Respond with JSON only: {{"pass": true|false, "reason": "one sentence"}}"""

    response = client.chat.completions.create(
        model=JUDGE_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"},
    )
    data = json.loads(response.choices[0].message.content)
    return bool(data.get("pass")), str(data.get("reason", ""))


def evaluate_row_at(client: OpenAI, row: GoldenRow, api_url: str) -> EvalResult:
    answer, sources = ask_stream(row.question, api_url)
    det_ok, det_notes = run_deterministic_checks(row, answer, sources)

    if not det_ok:
        return EvalResult(row=row, answer=answer, sources=sources, passed=False, reason=det_notes[-1], checks=det_notes)

    passed, reason = llm_judge(client, row, answer)
    return EvalResult(
        row=row,
        answer=answer,
        sources=sources,
        passed=passed,
        reason=reason,
        checks=det_notes + [f"judge: {reason}"],
    )


def write_experiment(tier: str, results: list[EvalResult], pass_rate: float, passed: bool) -> Path:
    EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = EXPERIMENTS_DIR / f"{ts}_{tier}.csv"
    with open(out, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "tier", "category", "question", "passed", "reason",
            "answer", "source_count", "grading_notes",
        ])
        writer.writeheader()
        for r in results:
            writer.writerow({
                "id": r.row.id,
                "tier": r.row.tier,
                "category": r.row.category,
                "question": r.row.question,
                "passed": r.passed,
                "reason": r.reason,
                "answer": r.answer[:500],
                "source_count": len(r.sources),
                "grading_notes": r.row.grading_notes,
            })

    summary = {
        "tier": tier,
        "timestamp": ts,
        "pass_rate": pass_rate,
        "passed": passed,
        "threshold": GATE_THRESHOLDS[tier]["min_pass_rate"],
        "total": len(results),
        "passed_count": sum(1 for r in results if r.passed),
        "failed_ids": [r.row.id for r in results if not r.passed],
    }
    summary_path = EXPERIMENTS_DIR / f"{ts}_{tier}.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return out


def print_report(tier: str, results: list[EvalResult], pass_rate: float, gate_passed: bool) -> None:
    threshold = GATE_THRESHOLDS[tier]["min_pass_rate"]
    passed_n = sum(1 for r in results if r.passed)
    total = len(results)

    print()
    print("=" * 64)
    print("  CampusQ Quality Gate")
    print("=" * 64)
    print(f"  Tier       : {tier.upper()}")
    print(f"  Policy     : {GATE_THRESHOLDS[tier]['label']}")
    print(f"  Threshold  : {threshold:.0%}")
    print(f"  Result     : {passed_n}/{total} passed ({pass_rate:.1%})")
    print(f"  Gate       : {'✅ PASSED' if gate_passed else '❌ FAILED'}")
    print("=" * 64)

    if not gate_passed:
        print("\nFailures:")
        for r in results:
            if not r.passed:
                print(f"  • [{r.row.id}] {r.row.question[:60]}")
                print(f"    {r.reason}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="CampusQ automated quality gate")
    parser.add_argument("--tier", choices=["smoke", "core", "full"], default="smoke")
    parser.add_argument("--api-url", default=API_URL)
    parser.add_argument("--delay", type=float, default=0.4, help="Seconds between questions")
    args = parser.parse_args()

    api_url = args.api_url.rstrip("/")
    ensure_chat_auth(api_url)

    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY is required for the LLM judge.")
        return 2

    try:
        requests.get(api_url, timeout=5)
    except Exception as exc:
        print(f"ERROR: Cannot reach {api_url} — start the backend first. ({exc})")
        return 2

    all_rows = load_golden_rows()
    rows = rows_for_tier(all_rows, args.tier)
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    print(f"Running {args.tier} quality gate — {len(rows)} questions against {api_url}")

    results: list[EvalResult] = []
    for i, row in enumerate(rows, 1):
        print(f"[{i}/{len(rows)}] {row.id}: {row.question[:55]}…")
        try:
            result = evaluate_row_at(client, row, api_url)
        except Exception as exc:
            result = EvalResult(
                row=row, answer=f"[ERROR: {exc}]", sources=[], passed=False,
                reason=str(exc), checks=["exception during eval"],
            )
        status = "PASS" if result.passed else "FAIL"
        print(f"         → {status}: {result.reason[:80]}")
        results.append(result)
        time.sleep(args.delay)

    passed_n = sum(1 for r in results if r.passed)
    pass_rate = passed_n / len(results) if results else 0.0
    gate_passed = pass_rate >= GATE_THRESHOLDS[args.tier]["min_pass_rate"]

    out_csv = write_experiment(args.tier, results, pass_rate, gate_passed)
    print_report(args.tier, results, pass_rate, gate_passed)
    print(f"Results saved to {out_csv}")

    return 0 if gate_passed else 1


if __name__ == "__main__":
    sys.exit(main())
