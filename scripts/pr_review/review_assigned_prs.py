#!/usr/bin/env python3
"""Fetch and review GitHub PRs assigned to a user on CampusQ."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

DEFAULT_REPO = "retriive/campusq"
MAX_DIFF_CHARS = 80_000

# Files/patterns that determine required quality gate tier.
CORE_GATE_PATHS = {
    "backend/main.py",
    "backend/retrieval.py",
    "backend/citations.py",
    "backend/evals/datasets/golden.csv",
}
CORE_GATE_PREFIXES = (
    "backend/scrapers/",
)
SMOKE_GATE_PREFIXES = (
    "backend/",
)


def run_gh(args: list[str], *, repo: str | None = None) -> Any:
    cmd = ["gh", *args]
    if repo:
        cmd.extend(["--repo", repo])
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    if not result.stdout.strip():
        return None
    return json.loads(result.stdout)


def run_gh_text(args: list[str], *, repo: str | None = None) -> str:
    cmd = ["gh", *args]
    if repo:
        cmd.extend(["--repo", repo])
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout


def classify_gate(changed_paths: list[str]) -> str:
    for path in changed_paths:
        if path in CORE_GATE_PATHS:
            return "core"
        for prefix in CORE_GATE_PREFIXES:
            if path.startswith(prefix):
                return "core"
    for path in changed_paths:
        for prefix in SMOKE_GATE_PREFIXES:
            if path.startswith(prefix):
                return "smoke"
    return "none"


def check_pr_hygiene(body: str) -> dict[str, bool]:
    lower = (body or "").lower()
    return {
        "has_what_changed": "what changed" in lower,
        "has_why": "## why" in lower or "\nwhy\n" in lower,
        "has_how_to_test": "how to test" in lower,
        "mentions_quality_gate": "quality gate" in lower or "smoke" in lower or "core" in lower,
    }


def secret_patterns_in_diff(diff: str) -> list[str]:
    hits: list[str] = []
    needles = [
        ("OPENAI_API_KEY=", "Possible OpenAI key"),
        ("PINECONE_API_KEY=", "Possible Pinecone key"),
        ("sk-", "Possible OpenAI secret key prefix"),
        (".env", "Reference to .env file"),
    ]
    for line in diff.splitlines():
        for needle, label in needles:
            if needle in line and not line.strip().startswith("+"):
                continue
            if needle in line and line.strip().startswith("+"):
                if ".env.example" in line or "not in git" in line.lower():
                    continue
                hits.append(f"{label}: {line.strip()[:120]}")
    return hits[:10]


def _fetch_prs_assignee(user: str, repo: str) -> list[dict[str, Any]]:
    return run_gh(
        [
            "pr",
            "list",
            "--assignee",
            user,
            "--state",
            "open",
            "--json",
            "number,title,url,author,headRefName,createdAt,reviewDecision,isDraft",
        ],
        repo=repo,
    )


def _fetch_prs_reviewer(user: str, repo: str) -> list[dict[str, Any]]:
    assignee_token = user if user != "@me" else "@me"
    return run_gh(
        [
            "pr",
            "list",
            "--search",
            f"review-requested:{assignee_token} is:open",
            "--json",
            "number,title,url,author,headRefName,createdAt,reviewDecision,isDraft",
        ],
        repo=repo,
    )


def list_prs(assignee: str, repo: str, as_json: bool, include_reviewer: bool) -> int:
    assignee_prs = _fetch_prs_assignee(assignee, repo)
    seen = {pr["number"] for pr in assignee_prs}
    prs = [{**pr, "assignment": "assignee"} for pr in assignee_prs]

    if include_reviewer:
        for pr in _fetch_prs_reviewer(assignee, repo):
            if pr["number"] not in seen:
                prs.append({**pr, "assignment": "reviewer"})
                seen.add(pr["number"])

    if as_json:
        print(json.dumps(prs, indent=2))
        return 0

    if not prs:
        label = "assigned to or awaiting review from"
        print(f"No open PRs {label} {assignee} in {repo}.")
        return 0

    print(f"Open PRs for {assignee} in {repo}:\n")
    for pr in prs:
        draft = " [DRAFT]" if pr.get("isDraft") else ""
        author = pr.get("author", {}).get("login", "?")
        role = pr.get("assignment", "assignee")
        print(f"  #{pr['number']}{draft}  {pr['title']}  ({role})")
        print(f"         {pr['url']}  (@{author}, branch: {pr['headRefName']})")
    return 0


def pr_context(number: int, repo: str, as_json: bool) -> int:
    pr = run_gh(
        [
            "pr",
            "view",
            str(number),
            "--json",
            "title,body,author,headRefName,baseRefName,additions,deletions,files,url,isDraft,reviewDecision",
        ],
        repo=repo,
    )
    diff = run_gh_text(["pr", "diff", str(number)], repo=repo)
    if len(diff) > MAX_DIFF_CHARS:
        diff = diff[:MAX_DIFF_CHARS] + f"\n\n... [diff truncated at {MAX_DIFF_CHARS} chars]"

    changed_paths = [f["path"] for f in pr.get("files", [])]
    hygiene = check_pr_hygiene(pr.get("body", ""))
    gate = classify_gate(changed_paths)
    secrets = secret_patterns_in_diff(diff)

    context = {
        "number": number,
        "url": pr["url"],
        "title": pr["title"],
        "author": pr.get("author", {}).get("login"),
        "head_ref": pr["headRefName"],
        "base_ref": pr["baseRefName"],
        "is_draft": pr.get("isDraft", False),
        "additions": pr.get("additions"),
        "deletions": pr.get("deletions"),
        "changed_files": changed_paths,
        "required_gate": gate,
        "pr_hygiene": hygiene,
        "possible_secrets_in_diff": secrets,
        "diff": diff,
        "review_hints": build_review_hints(gate, hygiene, secrets, changed_paths),
    }

    if as_json:
        print(json.dumps(context, indent=2))
        return 0

    print(f"PR #{number}: {pr['title']}")
    print(f"URL: {pr['url']}")
    print(f"Author: @{context['author']}  Branch: {pr['headRefName']} → {pr['baseRefName']}")
    print(f"Changes: +{pr.get('additions', 0)} / -{pr.get('deletions', 0)} across {len(changed_paths)} files")
    print(f"Required quality gate: {gate}")
    print()
    print("PR hygiene:")
    for key, ok in hygiene.items():
        print(f"  {'✓' if ok else '✗'} {key.replace('_', ' ')}")
    if secrets:
        print("\n⚠ Possible secrets in diff:")
        for s in secrets:
            print(f"  - {s}")
    print("\nReview hints:")
    for hint in context["review_hints"]:
        print(f"  - {hint}")
    print("\n--- diff ---\n")
    print(diff)
    return 0


def build_review_hints(
    gate: str,
    hygiene: dict[str, bool],
    secrets: list[str],
    changed_paths: list[str],
) -> list[str]:
    hints: list[str] = []
    if gate == "core":
        hints.append("Backend core files changed — require core gate (≥27/32) noted in PR.")
    elif gate == "smoke":
        hints.append("Backend changed — require smoke gate (10/10) noted in PR.")
    else:
        hints.append("Docs/frontend-only — quality gate may be N/A if no chat API impact.")

    if not hygiene["has_what_changed"]:
        hints.append("PR body missing 'What changed' section.")
    if not hygiene["has_why"]:
        hints.append("PR body missing 'Why' section.")
    if not hygiene["has_how_to_test"]:
        hints.append("PR body missing 'How to test' section.")
    if gate != "none" and not hygiene["mentions_quality_gate"]:
        hints.append("PR body does not mention quality gate results.")

    if "backend/main.py" in changed_paths:
        hints.append("System prompt change — verify existing smoke/core tests still pass.")
    if "backend/evals/datasets/golden.csv" in changed_paths:
        hints.append("golden.csv edited — confirm with Mahad before changing thresholds.")
    if any(p.startswith("backend/scrapers/") for p in changed_paths):
        hints.append("Scraper change — suggest core gate after re-index.")
    if secrets:
        hints.append("Possible secrets detected — block merge until resolved.")

    return hints


def post_review(number: int, event: str, body_file: Path, repo: str) -> int:
    body = body_file.read_text(encoding="utf-8")
    run_gh_text(
        [
            "pr",
            "review",
            str(number),
            "--event",
            event,
            "--body",
            body,
        ],
        repo=repo,
    )
    print(f"Posted {event} review on PR #{number} in {repo}.")
    return 0


def main() -> int:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--repo", default=DEFAULT_REPO, help="GitHub repo (owner/name)")
    common.add_argument("--json", action="store_true", help="JSON output")

    parser = argparse.ArgumentParser(description="CampusQ PR review helper")
    sub = parser.add_subparsers(dest="command", required=True)

    list_cmd = sub.add_parser("list", help="List open PRs assigned to user", parents=[common])
    list_cmd.add_argument("--assignee", default="@me", help="GitHub assignee (@me or username)")
    list_cmd.add_argument(
        "--include-reviewer",
        action="store_true",
        help="Also include PRs where user is a requested reviewer",
    )

    ctx_cmd = sub.add_parser("context", help="Fetch PR context for review", parents=[common])
    ctx_cmd.add_argument("--number", type=int, required=True)

    post_cmd = sub.add_parser("post", help="Post a review to GitHub", parents=[common])
    post_cmd.add_argument("--number", type=int, required=True)
    post_cmd.add_argument(
        "--event",
        choices=["APPROVE", "REQUEST_CHANGES", "COMMENT"],
        default="COMMENT",
    )
    post_cmd.add_argument("--body-file", type=Path, required=True)

    args = parser.parse_args()

    try:
        if args.command == "list":
            return list_prs(args.assignee, args.repo, args.json, args.include_reviewer)
        if args.command == "context":
            return pr_context(args.number, args.repo, args.json)
        if args.command == "post":
            return post_review(args.number, args.event, args.body_file, args.repo)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
