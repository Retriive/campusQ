"""Tests for signed-in user chat store."""

from pathlib import Path

import pytest

import user_store


def test_put_and_get_chats(tmp_path: Path):
    store = user_store.UserStore(db_path=str(tmp_path / "user_data.db"))
    payload = {
        "sessions": [{"id": "1", "title": "COMP 2402 prereqs", "createdAt": 100}],
        "messagesBySession": {
            "1": [
                {"id": "m1", "role": "user", "content": "What are the prereqs for COMP 2402?"},
                {"id": "m2", "role": "assistant", "content": "COMP 2401."},
            ]
        },
        "updatedAt": 100,
    }
    saved = store.put_chats("user_abc", payload)
    assert saved["sessions"][0]["id"] == "1"
    loaded = store.get_chats("user_abc")
    assert loaded["messagesBySession"]["1"][1]["content"] == "COMP 2401."


def test_get_missing_user_returns_empty(tmp_path: Path):
    store = user_store.UserStore(db_path=str(tmp_path / "user_data.db"))
    empty = store.get_chats("nobody")
    assert empty["sessions"] == []
    assert empty["messagesBySession"] == {}


def test_sanitize_drops_unknown_roles_and_caps_sessions():
    sessions = [{"id": str(i), "title": f"t{i}", "createdAt": i} for i in range(30)]
    msgs = {str(i): [{"id": "x", "role": "user", "content": "hi"}, {"id": "y", "role": "system", "content": "nope"}] for i in range(5)}
    cleaned = user_store.sanitize_chat_payload({
        "sessions": sessions,
        "messagesBySession": msgs,
        "updatedAt": 1,
    })
    assert len(cleaned["sessions"]) == user_store.MAX_SESSIONS
    assert all(m["role"] != "system" for msgs in cleaned["messagesBySession"].values() for m in msgs)


def test_sanitize_rejects_oversized_payload():
    huge = "x" * 50_000
    sessions = [{"id": str(i), "title": "t", "createdAt": i} for i in range(20)]
    messages = {
        str(i): [{"id": f"{i}-{j}", "role": "assistant", "content": huge} for j in range(40)]
        for i in range(20)
    }
    with pytest.raises(ValueError, match="too large"):
        user_store.sanitize_chat_payload({
            "sessions": sessions,
            "messagesBySession": messages,
            "updatedAt": 1,
        })


def test_delete_chats(tmp_path: Path):
    store = user_store.UserStore(db_path=str(tmp_path / "user_data.db"))
    store.put_chats("user_abc", {
        "sessions": [{"id": "1", "title": "Hi", "createdAt": 1}],
        "messagesBySession": {"1": [{"id": "m", "role": "user", "content": "hi"}]},
        "updatedAt": 1,
    })
    store.delete_chats("user_abc")
    assert store.get_chats("user_abc")["sessions"] == []
