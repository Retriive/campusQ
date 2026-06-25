"""
send_team_brief.py — The weekly INTERNAL team brief (Monday morning).

The founder/team pulse: usage, growth, retention, quality, and what needs
attention. DIFFERENT from send_digest.py (the external, anonymized ADVISOR
digest sent to university advisors).

In production this is sent automatically by an in-process scheduler inside the
always-on backend (see _start_brief_scheduler in main.py) so it can read the
logs on the persistent /data disk. Set ENABLE_BRIEF_SCHEDULER=true on the
backend to arm it.

You can also run it by hand for a one-off send or a local preview:
    py send_team_brief.py

Env vars (backend/.env):
    RESEND_API_KEY  — Resend API key                 (https://resend.com)
    TEAM_EMAILS     — comma-separated recipients      (default: team@retriive.com)
    BRIEF_FROM      — verified sender, e.g. "CampusQ <digest@retriive.com>"

Without RESEND_API_KEY it writes an HTML preview and prints the brief (dry-run).
"""

import os
from dotenv import load_dotenv
from dashboard import build_team_brief, build_team_brief_html

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

# Match main.py: logs live on the persistent /data disk on Render, else locally.
LOG_DIR = "/data" if os.path.isdir("/data") else os.path.dirname(os.path.abspath(__file__))


def send_brief(log_dir: str = LOG_DIR, *, quiet: bool = False) -> dict:
    """
    Build and send the team brief. Returns a status dict.
    With no RESEND_API_KEY/recipients it writes an HTML preview and returns
    {"sent": False} instead of sending. Raises on an actual send failure.
    """
    text = build_team_brief(log_dir)
    html = build_team_brief_html(log_dir)

    api_key = os.getenv("RESEND_API_KEY")
    recipients = [e.strip() for e in os.getenv("TEAM_EMAILS", "team@retriive.com").split(",") if e.strip()]
    sender = os.getenv("BRIEF_FROM", "CampusQ <onboarding@resend.dev>")

    if not api_key or not recipients:
        preview = os.path.join(log_dir, "team_brief_preview.html")
        with open(preview, "w", encoding="utf-8") as f:
            f.write(html)
        if not quiet:
            print("=== DRY RUN (no RESEND_API_KEY / TEAM_EMAILS set) ===\n")
            print(text)
            print(f"\nHTML preview written to: {preview}")
            print("\n=== set RESEND_API_KEY + BRIEF_FROM in .env to actually send ===")
        return {"sent": False, "reason": "dry-run"}

    import resend
    resend.api_key = api_key
    resend.Emails.send({
        "from": sender,
        "to": recipients,
        "subject": "CampusQ - Weekly Team Brief",
        "html": html,
        "text": text,
    })
    if not quiet:
        print(f"Team brief sent to {len(recipients)} recipient(s): {', '.join(recipients)}")
    return {"sent": True, "recipients": recipients}


def main():
    try:
        send_brief(LOG_DIR)
    except ImportError:
        print("The 'resend' package isn't installed. Run:  py -m pip install resend")
        raise SystemExit(1)
    except Exception as e:
        print(f"Failed to send team brief: {e}\n")
        print("Most common cause: the sender domain isn't verified in Resend.")
        print("  - Verify your domain at https://resend.com/domains, OR")
        print('  - Test now with BRIEF_FROM="CampusQ <onboarding@resend.dev>"')
        print("    and TEAM_EMAILS set to the email you signed up to Resend with.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
