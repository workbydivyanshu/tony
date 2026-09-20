"""tests/test_kimi_bridge.py — H1 Kimi seam freeze spec.

lib/kimi.py does not exist yet (RED). The module import itself is the
frozen-spec RED: `import lib.kimi` raises ModuleNotFoundError, which is
the correct greenfield-seam signal (P23 precedent: ModuleNotFoundError
lib.doctor).

The seam the implementer builds (this file is the spec):
  post(action, args, session, caller)   -> caller(payload) injected;
      default caller does urllib POST to http://127.0.0.1:10086/command
  status(caller)                        -> {up: bool, detail: str}
  list_tabs(session, caller)            -> parses [{tabId, url, title, active}]
  snapshot(session, caller)             -> {url, title, tree} passthrough
  read_page_text(session, caller)       -> compact string; fallback to tree text
  find_element_text(session, ref, caller) -> textContent string
  navigate(session, url, caller)        -> passes url + new_tab/group; returns caller dict
  scan_subjects(items, keywords)        -> PURE, no caller; case-insensitive substring

Every IO path is caller-injected. Zero daemon/browser/HTTP contact,
zero model calls, zero sleep.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import lib.kimi  # noqa: F401 — seam pin; lib/kimi.py does not exist yet (RED)


# ── caller fakes (injected everywhere IO happens) ──────────────────────

def _fake_caller_ok(payload):
    """Fake caller that returns an {ok...} response dict."""
    assert isinstance(payload, dict), f"payload must be dict, got {type(payload)}"
    assert "action" in payload, f"payload missing 'action' key: {payload}"
    assert "args" in payload, f"payload missing 'args' key: {payload}"
    assert "session" in payload, f"payload missing 'session' key: {payload}"
    return {"ok": True, "value": "done"}


def _fake_caller_refused():
    """Fake caller that raises ConnectionRefusedError (daemon not running)."""
    raise ConnectionRefusedError("Connection refused to 127.0.0.1:10086")


def _fake_caller_oserror():
    """Fake caller that raises OSError (network-level failure)."""
    raise OSError(9, "Bad file descriptor")


def _fake_caller_tabs():
    """Fake caller returning the exact tab-list shape."""
    return {
        "ok": True,
        "tabs": [
            {"tabId": "t1", "url": "https://example.com", "title": "Example", "active": True},
            {"tabId": "t2", "url": "https://google.com", "title": "Google", "active": False},
        ],
    }


def _fake_caller_snapshot():
    """Fake caller returning the exact snapshot shape."""
    return {
        "ok": True,
        "url": "https://example.com",
        "title": "Example Page",
        "tree": "<div>hello</div>",
    }


def _fake_caller_evaluate():
    """Fake caller returning an evaluate-style response with text."""
    return {"ok": True, "result": {"value": "compact text content"}}


def _fake_caller_evaluate_missing():
    """Fake caller returning a response without evaluate key (tree fallback)."""
    return {"ok": True, "tree": "<p>fallback text</p>"}


def _fake_caller_element():
    """Fake caller returning an element with textContent."""
    return {"ok": True, "element": {"textContent": "Submit"}}


def _fake_caller_navigate():
    """Fake caller returning a navigate result dict."""
    return {"ok": True, "tabId": "new_tab", "url": "https://example.com"}


# ── Tests ──────────────────────────────────────────────────────────────

def test_post_payload_shape():
    """post() builds {action, args, session} top-level; caller receives it.

    The fake caller asserts the payload has action/args/session keys,
    pinning the shape. Default caller does urllib POST to
    http://127.0.0.1:10086/command (implementer's business).
    """
    captured = []
    def capturing_caller(payload):
        captured.append(payload)
        return {"ok": True}
    lib.kimi.post("click", {"x": 1}, "s1", caller=capturing_caller)
    assert len(captured) == 1, "caller must be invoked exactly once"
    p = captured[0]
    assert set(p.keys()) == {"action", "args", "session"}, f"payload keys: {p.keys()}"
    assert p["action"] == "click"
    assert p["args"] == {"x": 1}
    assert p["session"] == "s1"


def test_post_default_caller_urllib():
    """post() with no caller does urllib POST to http://127.0.0.1:10086/command.

    Shape pinned via fake callers above; default is implementer's business.
    """
    # lib.kimi.post("navigate", {"url": "https://example.com"}, "s1")
    # would POST to http://127.0.0.1:10086/command with the payload.
    pass  # default caller is implementer's concern; shape pinned by fakes.


def test_status_up_true_on_ok_response():
    """status(caller) returns {up: True, detail: ...} when caller returns {ok...}."""
    result = lib.kimi.status(caller=_fake_caller_ok)
    assert result["up"] is True, f"expected up=True, got {result}"
    assert "detail" in result, "status must carry detail key"


def test_status_up_false_on_connection_refused():
    """status(caller) returns up=False with recovery command on ConnectionRefusedError.

    Recovery command must name the exact path: ~/.kimi-webbridge/bin/kimi-webbridge start
    """
    result = lib.kimi.status(caller=_fake_caller_refused)
    assert result["up"] is False, f"expected up=False, got {result}"
    assert "~/.kimi-webbridge/bin/kimi-webbridge start" in result["detail"], \
        f"detail must name recovery command; got {result['detail']}"


def test_status_up_false_on_oserror():
    """status(caller) returns up=False on OSError with recovery command."""
    result = lib.kimi.status(caller=_fake_caller_oserror)
    assert result["up"] is False, f"expected up=False, got {result}"
    assert "~/.kimi-webbridge/bin/kimi-webbridge start" in result["detail"], \
        f"detail must name recovery command; got {result['detail']}"


def test_list_tabs_parses_tab_structure():
    """list_tabs(session, caller) parses [{tabId, url, title, active}] from caller response."""
    tabs = lib.kimi.list_tabs("s1", caller=_fake_caller_tabs)
    assert len(tabs) == 2, f"expected 2 tabs, got {len(tabs)}"
    assert tabs[0]["tabId"] == "t1"
    assert tabs[0]["url"] == "https://example.com"
    assert tabs[0]["title"] == "Example"
    assert tabs[0]["active"] is True
    assert tabs[1]["tabId"] == "t2"
    assert tabs[1]["active"] is False


def test_snapshot_passthrough():
    """snapshot(session, caller) returns {url, title, tree} passthrough."""
    result = lib.kimi.snapshot("s1", caller=_fake_caller_snapshot)
    assert set(result.keys()) == {"url", "title", "tree"}, f"keys: {result.keys()}"
    assert result["url"] == "https://example.com"
    assert result["title"] == "Example Page"
    assert result["tree"] == "<div>hello</div>"


def test_read_page_text_from_evaluate():
    """read_page_text(session, caller) returns compact string from evaluate-style response."""
    text = lib.kimi.read_page_text("s1", caller=_fake_caller_evaluate)
    assert text == "compact text content", f"expected compact string, got {text!r}"


def test_read_page_text_fallback_to_tree():
    """read_page_text(session, caller) falls back to tree text when evaluate missing."""
    text = lib.kimi.read_page_text("s1", caller=_fake_caller_evaluate_missing)
    assert "fallback text" in text, f"expected tree text fallback, got {text!r}"


def test_find_element_text():
    """find_element_text(session, ref, caller) returns textContent string for the ref."""
    text = lib.kimi.find_element_text("s1", "submit-btn", caller=_fake_caller_element)
    assert text == "Submit", f"expected textContent 'Submit', got {text!r}"


def test_navigate_passes_url_and_new_tab():
    """navigate(session, url, caller) passes url + new_tab/group semantics through; returns caller dict."""
    result = lib.kimi.navigate("s1", "https://example.com", caller=_fake_caller_navigate)
    assert result["ok"] is True
    assert result["url"] == "https://example.com"


def test_scan_subjects_pure_case_insensitive():
    """scan_subjects(items, keywords) is PURE (no caller arg): case-insensitive substring match.

    Matches on subject+sender fields. Returns hits list.
    """
    items = [
        {"subject": "Meeting Reminder", "sender": "Alice"},
        {"subject": "Weekly Report", "sender": "Bob"},
        {"subject": "URGENT: Deadline", "sender": "Charlie"},
    ]
    hits = lib.kimi.scan_subjects(items, ["urgent", "deadline"])
    assert len(hits) == 1, f"expected 1 hit, got {hits}"
    assert hits[0]["subject"] == "URGENT: Deadline"


def test_scan_subjects_buildbear_negative_control():
    """buildbear-negative-control: items mentioning 'buildbear' with keywords lacking it -> excluded.

    Pure function, no caller. Case-insensitive substring match must NOT
    return items whose subject/sender mentions 'buildbear' when keywords
    do not contain 'buildbear'.
    """
    items = [
        {"subject": "buildbear deployment", "sender": "CI"},
        {"subject": "Normal task", "sender": "Dev"},
    ]
    hits = lib.kimi.scan_subjects(items, ["normal"])
    assert not any("buildbear" in h["subject"].lower() for h in hits), \
        f"buildbear item must be excluded; got {hits}"
    assert len(hits) == 1, f"expected 1 hit (non-buildbear), got {hits}"


def test_scan_subjects_empty_keywords():
    """scan_subjects(items, []) returns empty list (no keywords = no matches)."""
    items = [{"subject": "Anything", "sender": "Someone"}]
    hits = lib.kimi.scan_subjects(items, [])
    assert hits == [], f"empty keywords must yield empty hits; got {hits}"


def test_absence_pin_write_actions_unrepresentable():
    """lib.kimi exposes NONE of [click, fill, upload, cdp, network, close_tab, close_session].

    getattr(Lib, None) default makes write actions unrepresentable —
    the seam intentionally omits them.
    """
    forbidden = ["click", "fill", "upload", "cdp", "network", "close_tab", "close_session"]
    for name in forbidden:
        assert getattr(lib.kimi, name, None) is None, \
            f"lib.kimi must NOT expose {name!r}; write actions are unrepresentable"
