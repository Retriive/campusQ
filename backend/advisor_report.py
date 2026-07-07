"""
advisor_report.py — The external, advisor-facing weekly report.

This is the report we put in front of Carleton advising & student services
staff. Unlike the internal team brief (send_team_brief.py — usage, growth,
retention), this is framed entirely around what's useful to *them*:

  1. What students asked most this week (clustered, with counts)
  2. Questions students couldn't find official answers to — i.e. content gaps
     on the university's own web presence
  3. How much of this happened outside office hours

Everything is aggregated and anonymized: question text and counts only, no
names, no user IDs. Builders are pure functions over log_dir, same contract
as dashboard.py.
"""

import html as _html
from datetime import datetime

from dashboard import build_gap_report_data

SCHOOL_NAME = "Carleton University"


def build_advisor_report_text(log_dir: str) -> str:
    d = build_gap_report_data(log_dir)
    t = d["totals"]
    now = datetime.utcnow()

    cov = f"{t['coverage_pct']}%" if t["coverage_pct"] is not None else "n/a"
    aft = f"{t['after_hours_pct']}%" if t["after_hours_pct"] is not None else "n/a"

    L = []
    L.append("CampusQ — Student Questions Report")
    L.append(f"{SCHOOL_NAME} · " + now.strftime("Week of %B %d, %Y"))
    L.append("Prepared for advising & student services")
    L.append("=" * 48)
    L.append("")
    L.append("THE WEEK AT A GLANCE")
    L.append(f"  Questions students asked         : {t['questions']}")
    L.append(f"  Answered from official sources   : {cov}")
    L.append(f"  Asked outside office hours       : {aft}")
    L.append("")

    L.append("WHAT STUDENTS ASKED MOST")
    if d["top_asked"]:
        for i, row in enumerate(d["top_asked"][:5], 1):
            L.append(f"  {i}. \"{row['question']}\" — asked {row['count']}x")
    else:
        L.append("  (no answered questions in this window)")
    L.append("")

    prev = t["unanswered_prev_window"]
    trend = f" (prev. week: {prev})" if prev else ""
    L.append(f"WHERE STUDENTS COULDN'T FIND ANSWERS — {t['unanswered']} questions{trend}")
    L.append("  These had no clear answer in official public web content.")
    L.append("  Each is a candidate for a website/FAQ update — students are")
    L.append("  looking for this information and not finding it.")
    if d["gaps"]:
        for g in d["gaps"][:8]:
            L.append(f"  [{g['theme']}]")
            L.append(f"    \"{g['question']}\" — {g['count']}x")
            for v in g["variants"][:2]:
                L.append(f"      also phrased: \"{v}\"")
    else:
        L.append("  (none this week)")
    L.append("")
    L.append("All data is aggregated and anonymized — question text and counts")
    L.append("only, never student names or identifiers.")
    L.append("")
    L.append("— CampusQ · questions about this report: reply to this email")
    return "\n".join(L)


def build_advisor_report_html(log_dir: str) -> str:
    """Light, professional HTML email version. Inline styles only (email
    clients strip <style> blocks). 640px single column."""
    C = {
        "bg": "#f4f5f7", "card": "#ffffff", "border": "#e3e6ea",
        "text": "#1a202c", "muted": "#64707d", "accent": "#8b1d2c",
        "chip_bg": "#f7f2f3", "good": "#1a7f4b", "amber": "#946200",
    }
    FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"

    d = build_gap_report_data(log_dir)
    t = d["totals"]
    now = datetime.utcnow()
    esc = _html.escape

    def hero(value, label):
        return (
            f'<td align="center" width="33%" style="padding:16px 4px;font-family:{FONT};">'
            f'<div style="font-size:32px;line-height:1;font-weight:800;color:{C["text"]};">{value}</div>'
            f'<div style="margin-top:7px;font-size:11px;font-weight:600;letter-spacing:.8px;'
            f'text-transform:uppercase;color:{C["muted"]};">{label}</div></td>'
        )

    def section(title, inner, note=""):
        note_html = (
            f'<div style="margin-top:14px;padding-top:11px;border-top:1px solid {C["border"]};'
            f'font-size:12px;line-height:1.55;color:{C["muted"]};">{note}</div>'
        ) if note else ""
        return (
            f'<tr><td style="padding:7px 24px;">'
            f'<table width="100%" cellpadding="0" cellspacing="0" role="presentation" '
            f'style="background:{C["card"]};border:1px solid {C["border"]};border-radius:12px;">'
            f'<tr><td style="padding:18px 20px 15px;font-family:{FONT};">'
            f'<div style="font-size:12px;font-weight:700;letter-spacing:1.2px;text-transform:uppercase;'
            f'color:{C["accent"]};margin-bottom:12px;">{title}</div>{inner}{note_html}'
            f'</td></tr></table></td></tr>'
        )

    cov = f"{t['coverage_pct']}%" if t["coverage_pct"] is not None else "–"
    aft = f"{t['after_hours_pct']}%" if t["after_hours_pct"] is not None else "–"

    # ── Top asked ──
    if d["top_asked"]:
        asked = ""
        for row in d["top_asked"][:5]:
            asked += (
                f'<div style="font-size:14px;color:{C["text"]};line-height:1.5;padding:7px 0;'
                f'border-bottom:1px solid {C["border"]};font-family:{FONT};">'
                f'&ldquo;{esc(row["question"])}&rdquo; '
                f'<span style="color:{C["accent"]};font-weight:600;white-space:nowrap;">&times;{row["count"]}</span></div>'
            )
    else:
        asked = f'<div style="font-size:14px;color:{C["muted"]};font-family:{FONT};">No questions in this window.</div>'

    # ── Gaps ──
    if d["gaps"]:
        gaps = ""
        for g in d["gaps"][:8]:
            variants = ""
            for v in g["variants"][:2]:
                variants += (
                    f'<div style="font-size:12px;color:{C["muted"]};padding:2px 0 0 14px;'
                    f'font-family:{FONT};">also phrased: &ldquo;{esc(v)}&rdquo;</div>'
                )
            gaps += (
                f'<div style="padding:9px 0;border-bottom:1px solid {C["border"]};font-family:{FONT};">'
                f'<span style="display:inline-block;background:{C["chip_bg"]};color:{C["accent"]};'
                f'border-radius:20px;padding:2px 10px;font-size:11px;font-weight:600;">{esc(g["theme"])}</span>'
                f'<div style="margin-top:5px;font-size:14px;color:{C["text"]};line-height:1.5;">'
                f'&ldquo;{esc(g["question"])}&rdquo; '
                f'<span style="color:{C["amber"]};font-weight:600;white-space:nowrap;">&times;{g["count"]}</span></div>'
                f'{variants}</div>'
            )
    else:
        gaps = f'<div style="font-size:14px;color:{C["good"]};font-family:{FONT};">No unanswered questions this week.</div>'

    prev = t["unanswered_prev_window"]
    gap_note = (
        "Each item had no clear answer in official public web content — students are looking "
        "for this information and not finding it. These are candidates for a website or FAQ update."
        + (f" Previous week: {prev} unanswered." if prev else "")
    )

    week_label = now.strftime("Week of %B %d, %Y")

    return f"""\
<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:{C['bg']};">
<table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="background:{C['bg']};padding:24px 0;">
<tr><td align="center">
<table width="640" cellpadding="0" cellspacing="0" role="presentation" style="max-width:640px;width:100%;">

  <tr><td style="padding:8px 24px 0;font-family:{FONT};">
    <table width="100%" cellpadding="0" cellspacing="0" role="presentation"><tr>
      <td style="font-size:19px;font-weight:800;color:{C['text']};letter-spacing:-.3px;">
        <span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:{C['accent']};margin-right:8px;"></span>CampusQ</td>
      <td align="right" style="font-size:12px;font-weight:600;letter-spacing:.5px;text-transform:uppercase;color:{C['muted']};">Student Questions Report</td>
    </tr></table>
    <div style="margin-top:16px;font-size:24px;font-weight:800;color:{C['text']};">{week_label}</div>
    <div style="margin-top:4px;font-size:13px;color:{C['muted']};">{SCHOOL_NAME} &middot; prepared for advising &amp; student services</div>
    <div style="margin-top:16px;height:3px;border-radius:3px;background:{C['accent']};"></div>
  </td></tr>

  <tr><td style="padding:16px 24px 4px;">
    <table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="background:{C['card']};border:1px solid {C['border']};border-radius:12px;">
      <tr>{hero(t['questions'], "Questions asked")}{hero(cov, "Answered from official sources")}{hero(aft, "Outside office hours")}</tr>
    </table>
  </td></tr>

  {section("What students asked most", asked,
           "The most common questions this week, with near-duplicate phrasings grouped together.")}
  {section(f"Where students couldn&#39;t find answers &middot; {t['unanswered']}", gaps, gap_note)}

  <tr><td style="padding:18px 24px 8px;font-family:{FONT};text-align:center;">
    <div style="font-size:12px;color:{C['muted']};line-height:1.6;">
      All data is aggregated and anonymized &mdash; question text and counts only,<br>
      never student names or identifiers. Questions? Reply to this email.</div>
  </td></tr>

</table></td></tr></table></body></html>"""
