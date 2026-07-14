"""Tests for waitlist append + self-serve unsubscribe."""

from pathlib import Path

from waitlist_store import append_waitlist, remove_waitlist_email, waitlist_path


def test_append_and_unsubscribe(tmp_path: Path):
    log_dir = str(tmp_path)
    append_waitlist(log_dir, "a@carleton.ca", "Carleton")
    append_waitlist(log_dir, "b@carleton.ca", "Carleton")
    append_waitlist(log_dir, "A@Carleton.ca", "uOttawa")  # same address, different case

    removed = remove_waitlist_email(log_dir, "a@carleton.ca")
    assert removed == 2

    text = Path(waitlist_path(log_dir)).read_text(encoding="utf-8")
    assert "a@carleton.ca" not in text.lower()
    assert "b@carleton.ca" in text


def test_unsubscribe_missing_is_noop(tmp_path: Path):
    assert remove_waitlist_email(str(tmp_path), "nobody@example.com") == 0
