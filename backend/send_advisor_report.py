"""
send_advisor_report.py — Email the weekly Student Questions Report to
university advising staff.

This is the external, advisor-facing report (advisor_report.py): what students
asked, and which questions had no answer in official web content. For the
internal team brief, see send_team_brief.py.

Like send_digest.py, this does NOT run on its own — schedule it (Monday
morning) with cron / Task Scheduler / your host's cron feature.

Env vars needed to actually send:
  RESEND_API_KEY   — your Resend API key  (https://resend.com)
  ADVISOR_EMAILS   — comma-separated recipients, e.g. "a@carleton.ca,b@carleton.ca"
  DIGEST_FROM      — verified sender, e.g. "CampusQ <reports@yourdomain.com>"

Without those, it prints the plain-text report to stdout (safe dry-run).

Run:  py send_advisor_report.py
Schedule (cron):  0 8 * * 1  cd /path/to/backend && python send_advisor_report.py
"""

import os
from dotenv import load_dotenv
from advisor_report import build_advisor_report_html, build_advisor_report_text

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

LOG_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    text = build_advisor_report_text(LOG_DIR)

    api_key = os.getenv("RESEND_API_KEY")
    recipients = [e.strip() for e in os.getenv("ADVISOR_EMAILS", "").split(",") if e.strip()]
    sender = os.getenv("DIGEST_FROM", "CampusQ <onboarding@resend.dev>")

    if not api_key or not recipients:
        print("=== DRY RUN (no RESEND_API_KEY or ADVISOR_EMAILS set) ===\n")
        print(text)
        print("\n=== set the env vars above to actually send ===")
        return

    try:
        import resend
    except ImportError:
        print("The 'resend' package isn't installed. Run:  pip install resend")
        print("\nReport that would have been sent:\n")
        print(text)
        return

    resend.api_key = api_key
    resend.Emails.send({
        "from": sender,
        "to": recipients,
        "subject": "CampusQ — Student Questions Report",
        "html": build_advisor_report_html(LOG_DIR),
        "text": text,
    })
    print(f"Advisor report sent to {len(recipients)} recipient(s).")


if __name__ == "__main__":
    main()
