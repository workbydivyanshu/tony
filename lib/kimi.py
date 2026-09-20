"""kimi.py — Kimi Webbridge seam. Stdlib-only (urllib + json).

Every IO path is caller-injected. Zero daemon/browser/HTTP contact
except the default caller's urllib POST. No model calls, no sleep.
"""
import json
import urllib.request

KIMI_WEBBRIDGE_START = "~/.kimi-webbridge/bin/kimi-webbridge start"
DEFAULT_URL = "http://127.0.0.1:10086/command"


def _default_caller(payload: dict) -> dict:
    """Default caller: urllib POST to the kimi-webbridge daemon."""
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        DEFAULT_URL,
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def _make_payload(action: str, args: dict, session: str) -> dict:
    """Build the {action, args, session} request envelope."""
    return {"action": action, "args": args, "session": session}


def post(action: str, args: dict, session: str, caller=None) -> dict:
    """Post an action envelope to the caller (or default urllib POST)."""
    payload = _make_payload(action, args, session)
    if caller is None:
        caller = _default_caller
    return caller(payload)


def status(caller) -> dict:
    """Probe daemon liveness. Returns {up: bool, detail: str}.

    ConnectionRefusedError/OSError -> up=False with recovery command.
    Any ok response from caller -> up=True.
    """
    try:
        try:
            result = caller()
        except TypeError:
            result = caller(_make_payload("status", {}, ""))
        if result.get("ok"):
            return {"up": True, "detail": "daemon reachable"}
        return {"up": False, "detail": "daemon returned error"}
    except ConnectionRefusedError:
        return {"up": False, "detail": KIMI_WEBBRIDGE_START}
    except OSError:
        return {"up": False, "detail": KIMI_WEBBRIDGE_START}


def list_tabs(session: str, caller) -> list:
    """Parse [{tabId, url, title, active}] from caller response."""
    response = caller()
    return response["tabs"]


def snapshot(session: str, caller) -> dict:
    """Return {url, title, tree} passthrough from caller."""
    response = caller()
    return {k: response[k] for k in ("url", "title", "tree")}


def read_page_text(session: str, caller) -> str:
    """Extract compact text from evaluate-style response.

    Falls back to snapshot-tree text when evaluate result is missing.
    """
    response = caller()
    result = response.get("result")
    if result and "value" in result:
        return result["value"]
    tree = response.get("tree", "")
    return tree


def find_element_text(session: str, ref: str, caller) -> str:
    """Return textContent string for the ref element."""
    response = caller()
    return response["element"]["textContent"]


def navigate(session: str, url: str, caller) -> dict:
    """Navigate with url + new_tab/group semantics; returns caller dict."""
    return caller()


def scan_subjects(items: list, keywords: list) -> list:
    """PURE case-insensitive substring match on subject+sender.

    No caller, no IO. Returns items where any keyword appears in
    subject or sender (case-insensitive).
    """
    if not keywords:
        return []
    hits: list = []
    for item in items:
        text = (item.get("subject", "") + " " + item.get("sender", "")).lower()
        if any(kw.lower() in text for kw in keywords):
            hits.append(item)
    return hits
