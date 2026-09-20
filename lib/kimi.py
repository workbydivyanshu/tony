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


_READ_CODE = ("(() => JSON.stringify({text: document.title + ' || ' + "
              "(document.body ? document.body.innerText : ''), next: "
              "!!([...document.querySelectorAll('button')].find(x => "
              "(x.textContent||'').trim() === 'Next page' && "
              "String(x.className||'').includes('tiny') && !x.disabled))}))()")

_TURN_CODE = ("(() => { const scope = document.querySelector('nav.mail-toolbar'); "
              "const btns = scope ? [...scope.querySelectorAll('button')] : "
              "[...document.querySelectorAll('button')]; const b = btns.find(x => "
              "(x.textContent||'').trim() === 'Next page' && "
              "String(x.className||'').includes('tiny') && !x.disabled); "
              "if (!b) return 'NO-NEXT'; b.click(); return 'TURNED'; })()")


def _default_ev(session: str):
    """Default ev: evaluate through post(). Read-only codes only."""
    def ev(code: str) -> str:
        res = post("evaluate", {"code": code}, session)
        data = res.get("data", res)
        val = data.get("value", "") if isinstance(data, dict) else data
        return val if isinstance(val, str) else str(val)
    return ev


def read_inbox_page(session: str, ev=None) -> dict:
    """Read current list page -> {text, has_next}. Never clicks."""
    if ev is None:
        ev = _default_ev(session)
    try:
        data = json.loads(ev(_READ_CODE))
    except (ValueError, TypeError):
        return {"text": "", "has_next": False}
    if not isinstance(data, dict):
        return {"text": "", "has_next": False}
    return {"text": data.get("text", ""), "has_next": bool(data.get("next"))}


def turn_inbox_page(session: str, ev=None) -> bool:
    """Click the list-toolbar Next pager (advances the LIST only; opens
    no emails, mutates no site data). Returns True when turned."""
    if ev is None:
        ev = _default_ev(session)
    try:
        return ev(_TURN_CODE) == "TURNED"
    except Exception:
        return False


def scan_inbox_pages(session: str, ev=None, keywords=(), max_pages: int = 12,
                     settle_fn=None) -> dict:
    """Walk list pages to the end (or max_pages): read, keyword-scan each
    page text via scan_subjects, turn while a next pager exists. Returns
    {pages, subjects, hits:[{page, subject}]}. settle_fn(seconds) runs
    after each turn so the next read sees the new page."""
    if ev is None:
        ev = _default_ev(session)
    kw = tuple(keywords or ())
    pages = 0
    subjects = 0
    hits: list = []
    while pages < max_pages:
        page = read_inbox_page(session, ev)
        pages += 1
        # P30 chrome-noise lesson: scan parsed ROWS, never whole-page text
        # (nav chrome false-hit 12/12 live). Marker-less pages = zero rows.
        rows = parse_inbox_rows(page["text"])
        subjects += len(rows)
        if kw:
            for h in scan_subjects(rows, list(kw)):
                hits.append({"page": pages, "sender": h.get("sender", "?"),
                             "subject": h.get("subject", "")[:200]})
        if not page["has_next"]:
            break
        if not turn_inbox_page(session, ev):
            break
        if settle_fn is not None:
            settle_fn(3)
    return {"pages": pages, "subjects": subjects, "hits": hits}


def parse_inbox_rows(text: str) -> list:
    """PURE: split Proton list text on 'Star conversation' markers into
    [{sender, subject}]. Sender = first line of each chunk, subject = the
    rest joined (date lines included — harmless for keyword scans).
    Marker-less text (login walls, empty) -> [] and never raises."""
    rows: list = []
    try:
        chunks = (text or "").split("Star conversation")
    except Exception:
        return []
    for chunk in chunks[1:]:
        lines = [ln.strip() for ln in chunk.splitlines() if ln.strip()]
        if not lines:
            continue
        rows.append({"sender": lines[0],
                     "subject": " ".join(lines[1:])})
    return rows
