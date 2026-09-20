"""inboxscan.py — deterministic Proton reply-check command (P31).

Zero model calls: bridge pages -> rows -> keyword scan -> report file +
desktop notify on hits ONLY (quiet days stay quiet, Hermes rule). The tony
--inbox-scan flag is a thin pass-through; everything pinnable lives here.
"""
import datetime as _dt
import os as _os

SCAN_KEYWORDS = ("interview", "offer", "applied", "rejected", "assessment",
                 "application submitted", "action required")
# NOTE: 'oa' deliberately excluded — 2-letter substring matches UI chrome
# (proven live: 12/12 false-hit run). Kept out by evidence, not taste.

SESSION = "tony-inbox-scan"
INBOX_URL = "https://mail.proton.me/"


def _default_scan(session: str, keywords: list, max_pages: int) -> dict:
    import time as _time
    from lib import kimi as _kimi
    return _kimi.scan_inbox_pages(session, None, keywords, max_pages,
                                  settle_fn=_time.sleep)


def _default_notify(title: str, body: str) -> None:
    from lib import daemon as _daemon
    _daemon.notify(title, body)


def _default_nav(session: str, url: str) -> bool:
    """Open the inbox in a fresh tab, then settle for first paint."""
    import time as _time
    from lib import kimi as _kimi
    _kimi.post("navigate", {"url": url, "newTab": True}, session)
    _time.sleep(8)
    return True


def run_scan(max_pages: int = 12, scan_fn=None, notify_fn=None,
             nav_fn=None, outdir: str | None = None) -> int:
    """Run one reply check. Returns 0 (scan completed) or 1 (infra fail).

    Writes exactly one report .md into outdir (default ~/.fleet/out).
    Notifies ONLY when keyword hits exist; infra failure and quiet days
    stay silent (the daemon loop logs the report path either way).
    """
    scan_fn = scan_fn or _default_scan
    notify_fn = notify_fn or _default_notify
    nav_fn = nav_fn or _default_nav
    outdir = outdir or _os.path.join(_os.path.expanduser("~"), ".fleet", "out")
    stamp = _dt.datetime.now().strftime("%Y-%m-%d")
    try:
        nav_fn(SESSION, INBOX_URL)
    except Exception as exc:
        return _write(outdir, stamp, None, None, f"infra failure: navigate: {exc!r}", 1)
    try:
        res = scan_fn(SESSION, list(SCAN_KEYWORDS), max_pages)
    except Exception as exc:
        return _write(outdir, stamp, None, None, f"infra failure: {exc!r}", 1)
    hits = res.get("hits", []) or []
    if res.get("subjects", 0) == 0 and not hits:
        verdict = "login required? pages read but zero rows parsed"
    elif hits:
        verdict = f"{len(hits)} reply signal(s)"
    else:
        verdict = "quiet — no reply signals"
    code = _write(outdir, stamp, res, hits, verdict, 0)
    if hits:
        lines = "\n".join(f"{h.get('sender', '?')}: {h.get('subject', '?')[:100]}"
                          for h in hits[:5])
        try:
            notify_fn(f"tony inbox: {len(hits)} reply signal(s)",
                      lines[:400])
        except Exception:
            pass
    return code


def _write(outdir: str, stamp: str, res, hits, verdict: str, code: int) -> int:
    _os.makedirs(outdir, exist_ok=True)
    if res is None:
        body = (f"# tony inbox scan {stamp}\n\nstatus: FAILED\n{verdict}\n")
    else:
        lines = [f"# tony inbox scan {stamp}", "",
                 f"pages: {res.get('pages', '?')}",
                 f"rows: {res.get('subjects', '?')}",
                 f"verdict: {verdict}", ""]
        for h in (hits or []):
            lines.append(f"- p{h.get('page', '?')} [{h.get('sender', '?')}] "
                         f"{h.get('subject', '')[:160]}")
        if not hits and res.get("subjects", 0):
            lines.append("quiet — no reply signals")
        body = "\n".join(lines) + "\n"
    with open(_os.path.join(outdir, f"tony-inbox-scan-{stamp}.md"), "w") as f:
        f.write(body)
    return code
