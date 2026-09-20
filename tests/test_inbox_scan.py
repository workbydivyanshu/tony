"""tests/test_inbox_scan.py — P30 paginated inbox scan units.

The ev(code)->str seam models the daemon faithfully: read calls are
idempotent (same page JSON until a turn), turn calls (code containing
'click') advance the page cursor. Fakes distinguish by CODE CONTENT —
the same way production does. Zero daemon/HTTP contact.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib import kimi


def _ev_script(pages):
    """Stateful ev fake over [(text, has_next)]: reads return current page
    JSON without advancing; click-codes advance the cursor ('TURNED')."""
    calls = []
    state = {"n": 0}

    def ev(code):
        calls.append(code)
        if "click" in code:
            state["n"] = min(state["n"] + 1, len(pages) - 1)
            return "TURNED"
        text, has_next = pages[state["n"]]
        return json.dumps({"text": text, "next": has_next})

    ev.calls = calls
    return ev


def test_read_page_returns_text_and_next_flag():
    """read_inbox_page returns {text, has_next}; read-code never clicks."""
    ev = _ev_script([("inbox mail list 1/12", True)])
    res = kimi.read_inbox_page("s1", ev)
    assert res["text"] == "inbox mail list 1/12", res
    assert res["has_next"] is True, res
    assert all("click" not in c for c in ev.calls), ev.calls


def test_read_page_last_page_no_next():
    """Final page: has_next False stops the loop; re-reads are stable."""
    ev = _ev_script([("last page 12/12", False)])
    first = kimi.read_inbox_page("s1", ev)
    second = kimi.read_inbox_page("s1", ev)
    assert first["has_next"] is False, first
    assert second["text"] == first["text"], (first, second)


def test_turn_page_clicks_toolbar_next():
    """turn_inbox_page clicks scoped to the list-toolbar Next and advances."""
    ev = _ev_script([("page one", True), ("page two", False)])
    ok = kimi.turn_inbox_page("s1", ev)
    assert ok is True, ok
    assert len(ev.calls) == 1, ev.calls
    assert "click" in ev.calls[0], ev.calls
    assert "mail-toolbar" in ev.calls[0], ev.calls
    res = kimi.read_inbox_page("s1", ev)
    assert res["text"] == "page two", res


def test_scan_loops_pages_and_hits_keyword():
    """3 scripted pages, keyword on page 3: 2 turns, 2 settles, 1 hit."""
    pages = [("page one Digest", True), ("page two Digest", True),
             ("page three INTERVIEW invite", False)]
    ev = _ev_script(pages)
    settled = []
    res = kimi.scan_inbox_pages("s1", ev, ("interview",), max_pages=12,
                                settle_fn=lambda s: settled.append(s))
    assert res["pages"] == 3, res
    assert res["subjects"] == 3, res
    assert len(res["hits"]) == 1, res
    assert res["hits"][0]["page"] == 3, res
    assert "INTERVIEW" in res["hits"][0]["subject"], res
    assert len(settled) == 2, settled  # settle after each turn, not after last


def test_parse_rows_splits_sender_subject():
    """Star-conversation-delimited chunks -> sender + joined subject."""
    text = ("Conversation list 3 unread messages\n"
            "Star conversation\nSWE List\n66 New Internships Posted Today\n"
            "Sep 18\nStar conversation\nLinkedIn\n"
            "Your LinkedIn account is now hibernating.\nSep 16\n")
    rows = kimi.parse_inbox_rows(text)
    assert len(rows) == 2, rows
    assert rows[0]["sender"] == "SWE List", rows
    assert "66 New Internships" in rows[0]["subject"], rows
    assert rows[1]["sender"] == "LinkedIn", rows
    assert "hibernating" in rows[1]["subject"], rows


def test_parse_rows_empty_without_markers():
    """Login-wall chrome (no markers) -> zero rows, never a crash."""
    assert kimi.parse_inbox_rows("Sign in\nEmail or phone\n") == []
    assert kimi.parse_inbox_rows("") == []
