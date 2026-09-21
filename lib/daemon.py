"""daemon.py — resident inbox loop (Hermes-replacement step 3). Stdlib only.

Inbox: ~/.tony/inbox/*.md (one mission per file; file content = mission text).
Claim: atomic rename to <name>.md.claimed so two daemons never run one job.
Done: ~/.tony/inbox-done/<name>.done.md holds the mission report.

run_once(inbox, mission_fn, home) executes the oldest pending mission via
mission_fn(text, stem) -> report string. loop() polls until stop_after jobs
or KeyboardInterrupt. Live CLI wires mission_fn to cmd_mission (headless,
--yes); tests inject fakes — no model burn at the seam.
"""
import os
import time

CLAIMED_SUFFIX = ".claimed"


def notify(title: str, body: str, run=None) -> None:
    """Desktop pulse on mission completion (terminal-native, no TTS).
    Best-effort: silently no-ops when notify-send is missing (headless)."""
    try:
        import subprocess
        run = run or subprocess.run
        run(["notify-send", "-a", "tony", title, body], capture_output=True, timeout=5)
    except Exception:
        pass


def inbox_dir(home: str | None = None) -> str:
    base = home or os.path.expanduser("~")
    return os.path.join(base, ".tony", "inbox")


def done_dir(home: str | None = None) -> str:
    base = home or os.path.expanduser("~")
    return os.path.join(base, ".tony", "inbox-done")


def list_pending(inbox: str) -> list:
    """Sorted pending mission paths. Skips claimed/done/hidden files."""
    try:
        names = sorted(os.listdir(inbox))
    except OSError:
        return []
    out = []
    for n in names:
        if not n.endswith(".md"):
            continue
        if n.endswith(CLAIMED_SUFFIX + ".md") or n.endswith(".claimed"):
            continue
        if n.endswith(".done.md"):
            continue
        if n.startswith("."):
            continue
        out.append(os.path.join(inbox, n))
    return out


def claim(path: str) -> str:
    """Atomically claim a mission file. Returns the claimed path."""
    dest = path + CLAIMED_SUFFIX
    os.rename(path, dest)
    return dest


def reap_stale_claims(inbox: str, ttl_minutes: int = 30, now: float | None = None) -> int:
    """Un-claim .claimed files whose mtime is older than the TTL.

    A killed daemon leaves .claimed files that list_pending never shows —
    without a reaper those missions are invisible forever. Mtime older than
    ttl_minutes -> rename back to the pending name. Returns reaped count.
    Fresh claims (live daemon holding them) are never touched.
    """
    if now is None:
        now = time.time()
    reaped = 0
    try:
        names = sorted(os.listdir(inbox))
    except OSError:
        return 0
    for n in names:
        if not n.endswith(CLAIMED_SUFFIX):
            continue
        cpath = os.path.join(inbox, n)
        try:
            age_min = (now - os.path.getmtime(cpath)) / 60
        except OSError:
            continue
        if age_min <= ttl_minutes:
            continue
        orig = cpath[: -len(CLAIMED_SUFFIX)]
        if os.path.exists(orig):
            continue  # never clobber a live pending file
        try:
            os.rename(cpath, orig)
            reaped += 1
        except OSError:
            pass
    return reaped


def _stem(path: str) -> str:
    base = os.path.basename(path)
    return base[:-3] if base.endswith(".md") else base


MISSION_FN_NONE_DISABLED = True


def run_once(inbox: str, mission_fn, home: str | None = None) -> dict | None:
    """Execute the oldest pending mission. Empty inbox -> None (noop).

    Each pass first reaps stale claims (killed-daemon orphans older than the
    TTL become visible again), then serves inbox missions, then due cron
    schedules (ledger-guarded, missed windows skipped, never backfilled).

    A None mission_fn disables the path with an honest BLOCKED record."""
    if mission_fn is None:
        return {"name": "", "status": "BLOCKED", "report_path": None}
    try:
        reap_stale_claims(inbox)
    except Exception:
        pass
    pending = list_pending(inbox)
    if not pending:
        from lib import sched as _sched
        try:
            return _sched.run_due(home, mission_fn)
        except Exception:
            return None
    src = pending[0]
    stem = _stem(src)
    try:
        claimed = claim(src)
    except FileNotFoundError:
        return None  # P25: lost the claim race — peer holds the job; yield, don't crash
    try:
        with open(claimed) as f:
            text = f.read()
    except OSError as e:
        try:
            os.rename(claimed, src)  # release: claimed files are invisible to list_pending
        except OSError:
            pass
        return {"name": stem, "status": f"read-fail: {e}", "report_path": None}
    try:
        report = mission_fn(text, stem)
        status = "ok"
    except Exception as e:  # one job's blowup never kills the daemon
        report = f"mission failed: {e}"
        status = "fail"
    ddir = done_dir(home)
    os.makedirs(ddir, exist_ok=True)
    rpath: str | None = None
    try:
        p = os.path.join(ddir, stem + ".done.md")
        with open(p, "w") as f:
            f.write(f"# {stem} — {status}\n\n{report}\n")
        rpath = p
    except OSError:
        rpath = None
    try:
        os.remove(claimed)
    except OSError:
        pass
    notify("tony: " + stem, f"mission {status} — report: {rpath}")
    return {"name": stem, "status": status, "report_path": rpath}


def loop(inbox: str, mission_fn, interval: int = 10, stop_after: int | None = None,
         sleep_fn=None, home: str | None = None) -> int:
    """Poll until stop_after jobs done (None = forever). Returns jobs run."""
    _sleep = sleep_fn or time.sleep
    done = 0
    while True:
        res = run_once(inbox, mission_fn, home=home)
        if res is not None:
            done += 1
            if stop_after is not None and done >= stop_after:
                return done
            continue
        if stop_after is not None and done >= stop_after:
            return done
        try:
            _sleep(interval)
        except KeyboardInterrupt:
            return done
