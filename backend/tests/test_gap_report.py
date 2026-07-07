"""Unit tests for question clustering and the advisor gap report."""

import json
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard import build_gap_report_data, cluster_questions
from advisor_report import build_advisor_report_html, build_advisor_report_text


# ── cluster_questions ─────────────────────────────────────────────────────────

def test_near_duplicates_merge_into_one_cluster():
    questions = [
        "when is the last day to drop a course",
        "when is the last day to drop a course",
        "When can I drop courses?",
        "last day to drop a course?",
    ]
    clusters = cluster_questions(questions)
    assert len(clusters) == 1
    assert clusters[0]["count"] == 4
    # Representative is the most common verbatim phrasing
    assert clusters[0]["question"] == "when is the last day to drop a course"
    # Other phrasings surface as variants
    assert len(clusters[0]["variants"]) == 2


def test_distinct_topics_stay_separate():
    questions = [
        "when is the last day to drop a course",
        "how much is tuition for international students",
        "what are the prerequisites for COMP 2402",
    ]
    clusters = cluster_questions(questions)
    assert len(clusters) == 3


def test_course_codes_cluster_together_across_spacing():
    questions = [
        "prerequisites for COMP 2402",
        "prerequisites for comp2402?",
    ]
    clusters = cluster_questions(questions)
    assert len(clusters) == 1
    assert clusters[0]["count"] == 2


def test_contractions_and_prereq_shorthand_merge():
    questions = [
        "when is the deadline to drop fall courses",
        "when's the deadline to drop fall courses?",
        "what are the prerequisites for COMP 2402",
        "prereqs for comp 2402",
    ]
    clusters = cluster_questions(questions)
    assert len(clusters) == 2
    assert all(c["count"] == 2 for c in clusters)


def test_junk_is_dropped():
    clusters = cluster_questions(["hi", "asdf", "???", "", "  ", "is the a to"])
    assert clusters == []


def test_sorted_by_count_desc():
    questions = ["how do I apply for co-op"] * 1 + ["when is the winter break"] * 3
    clusters = cluster_questions(questions)
    assert clusters[0]["question"] == "when is the winter break"
    assert [c["count"] for c in clusters] == sorted(
        [c["count"] for c in clusters], reverse=True
    )


# ── build_gap_report_data ─────────────────────────────────────────────────────

def _write_queries_log(tmp_path, rows):
    with open(os.path.join(tmp_path, "queries.log"), "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def _row(query, had_context=True, days_ago=1, session="s1", user="u1"):
    ts = (datetime.utcnow() - timedelta(days=days_ago)).isoformat() + "Z"
    return {"ts": ts, "query": query, "had_context": had_context,
            "session": session, "user": user}


def test_gap_report_counts_and_clusters(tmp_path):
    _write_queries_log(tmp_path, [
        _row("when is the fall reading week"),
        _row("when is fall reading week?"),
        _row("can I get a parking permit as a first year", had_context=False),
        _row("can first years get parking permits?", had_context=False),
        _row("how do I appeal a grade", had_context=False),
    ])
    d = build_gap_report_data(str(tmp_path))
    t = d["totals"]
    assert t["questions"] == 5
    assert t["answered"] == 2
    assert t["coverage_pct"] == 40
    assert t["unanswered"] == 3
    # The two parking questions cluster into one gap of count 2
    assert d["gaps"][0]["count"] == 2
    assert len(d["gaps"]) == 2
    # Every gap carries a human-readable theme
    assert all(g["theme"] for g in d["gaps"])


def test_gap_report_excludes_eval_traffic(tmp_path):
    _write_queries_log(tmp_path, [
        _row("when is the drop deadline"),
        _row("synthetic eval question", session="quality-gate"),
    ])
    d = build_gap_report_data(str(tmp_path))
    assert d["totals"]["questions"] == 1


def test_gap_report_window(tmp_path):
    _write_queries_log(tmp_path, [
        _row("recent question about deadlines", days_ago=1),
        _row("old question about deadlines", days_ago=30),
    ])
    d = build_gap_report_data(str(tmp_path), days=7)
    assert d["totals"]["questions"] == 1


def test_gap_report_empty_logs(tmp_path):
    d = build_gap_report_data(str(tmp_path))
    assert d["totals"]["questions"] == 0
    assert d["totals"]["coverage_pct"] is None
    assert d["gaps"] == []


# ── advisor report builders ───────────────────────────────────────────────────

def test_advisor_report_text_contains_gaps_and_no_user_ids(tmp_path):
    _write_queries_log(tmp_path, [
        _row("when is the fall reading week"),
        _row("can I get a parking permit as a first year",
             had_context=False, user="user_secret_123"),
    ])
    text = build_advisor_report_text(str(tmp_path))
    assert "parking permit" in text
    assert "Student Questions Report" in text
    assert "user_secret_123" not in text


def test_advisor_report_html_renders_and_escapes(tmp_path):
    _write_queries_log(tmp_path, [
        _row("<script>alert(1)</script> when is reading week", had_context=False),
    ])
    html = build_advisor_report_html(str(tmp_path))
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
    assert "Student Questions Report" in html
