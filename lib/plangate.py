"""plangate.py — omO-style pre-execution approval. Stdlib only.

After the architect plans and BEFORE any builder call, TTY missions pause
for y/N unless pre-approved (--yes). Headless (non-TTY) never blocks: it
proceeds with an honest log line so pipes/cron can't hang.
"""


def confirm_plan(b: dict, input_fn=None, is_tty: bool = False,
                 pre_approved: bool = False) -> bool:
    """Return True to execute, False to hold. Logs the decision on b."""
    log = b.setdefault("log", [])
    if pre_approved:
        log.append("plan-gate bypassed (--yes)")
        return True
    if not is_tty:
        log.append("plan-gate skipped (non-TTY headless)")
        return True
    read = input_fn or input
    try:
        ans = (read("Proceed with this plan? [y/N] ") or "").strip().lower()
    except (EOFError, KeyboardInterrupt):
        ans = ""
    if ans in ("y", "yes"):
        log.append("plan-gate approved by operator")
        return True
    log.append("plan-gate declined by operator — mission held")
    return False
