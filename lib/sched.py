"""sched.py — cron scheduler (P11). Stdlib only.

Cron: minute hour dom month dow (standard 5-field). Supports * , - / steps
plus mon..sun / jan..dec names. dom/dow use standard cron OR-semantics:
when BOTH are restricted (not *), a datetime matches if EITHER matches;
otherwise both must match. "Feb 30" style crons (e.g. 30 2 30 2 *) simply
never match any real datetime — no special-casing needed.

Store: ~/.tony/schedule.json (list of {name, cron, mission}).
Ledger: ~/.tony/schedule-ledger.json ({name: "YYYY-MM-DD HH:MM"} last fired).
Missed windows are SKIPPED, never backfilled: a job fires only when its cron
matches the current minute and the ledger shows it hasn't fired this minute.
The daemon is not a catch-up service.

run_due(home, mission_fn, now) executes the oldest due job via
mission_fn(mission_text, "sched-<name>") and marks the ledger. Tests inject
fakes + temp HOME — no model burn at the seam.
"""
import datetime as _dt
import json as _json
import os as _os

DOW_NAMES = {"sun": 0, "mon": 1, "tue": 2, "wed": 3, "thu": 4, "fri": 5, "sat": 6}
MONTH_NAMES = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
               "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}

# (lo, hi, names) per field: minute hour dom month dow
_FIELDS = ((0, 59, None), (0, 23, None), (1, 31, None),
           (1, 12, MONTH_NAMES), (0, 7, DOW_NAMES))


def _parse_atom(atom: str, lo: int, hi: int, names: dict | None) -> set:
    atom = atom.strip().lower()
    if names and atom in names:
        v = names[atom]
        return {7} if (hi == 7 and v == 0) else {v}
    try:
        v = int(atom, 10)
    except ValueError:
        raise ValueError(f"bad cron atom: {atom!r}")
    if not lo <= v <= hi:
        raise ValueError(f"cron value {v} out of range {lo}-{hi}")
    return {v}


def parse_field(field: str, lo: int, hi: int, names: dict | None = None) -> set:
    """Parse one cron field into a set of ints. '*' -> full range."""
    field = field.strip()
    if not field:
        raise ValueError("empty cron field")
    full = set(range(lo, hi + 1))
    if field == "*":
        return full
    out: set = set()
    for part in field.split(","):
        part = part.strip()
        if "/" in part:
            base, step_s = part.split("/", 1)
            try:
                step = int(step_s, 10)
            except ValueError:
                raise ValueError(f"bad cron step: {part!r}")
            if step < 1:
                raise ValueError(f"cron step must be >= 1: {part!r}")
            if base in ("*", ""):
                rng = full
            elif "-" in base:
                a_s, b_s = base.split("-", 1)
                a = next(iter(_parse_atom(a_s, lo, hi, names)))
                b = next(iter(_parse_atom(b_s, lo, hi, names)))
                if a > b:
                    raise ValueError(f"cron range reversed: {part!r}")
                rng = set(range(a, b + 1))
            else:
                a = next(iter(_parse_atom(base, lo, hi, names)))
                rng = set(range(a, hi + 1))
            out |= {v for v in rng if (v - min(rng)) % step == 0}
        elif "-" in part:
            a_s, b_s = part.split("-", 1)
            a = next(iter(_parse_atom(a_s, lo, hi, names)))
            b = next(iter(_parse_atom(b_s, lo, hi, names)))
            if a > b:
                raise ValueError(f"cron range reversed: {part!r}")
            out |= set(range(a, b + 1))
        else:
            out |= _parse_atom(part, lo, hi, names)
    if not out:
        raise ValueError(f"cron field matched nothing: {field!r}")
    return out


def parse_cron(expr: str) -> dict:
    """Parse a 5-field cron expression into {minute,hour,dom,month,dow} sets."""
    parts = expr.strip().split()
    if len(parts) != 5:
        raise ValueError(f"cron needs 5 fields, got {len(parts)}: {expr!r}")
    keys = ("minute", "hour", "dom", "month", "dow")
    return {k: parse_field(p, lo, hi, names)
            for k, p, (lo, hi, names) in zip(keys, parts, _FIELDS)}


def _dow_cron(dt: _dt.datetime) -> int:
    """Python Monday=0..Sunday=6 -> cron Sunday=0..Saturday=6."""
    return (dt.weekday() + 1) % 7


def matches(spec: dict, dt: _dt.datetime) -> bool:
    """True when datetime dt falls inside the parsed cron spec."""
    if dt.minute not in spec["minute"]:
        return False
    if dt.hour not in spec["hour"]:
        return False
    if dt.month not in spec["month"]:
        return False
    dom_full = len(spec["dom"]) == 31
    # dow full = all of 0..7 present, or all of 0..6 / 1..7 (Sunday aliased)
    dow = {0 if v == 7 else v for v in spec["dow"]}
    dow_full = len(dow) == 7
    dom_ok = dt.day in spec["dom"]
    dow_ok = _dow_cron(dt) in dow
    if not dom_full and not dow_full:
        return dom_ok or dow_ok  # standard cron OR-semantics
    return dom_ok and dow_ok


def matches_expr(expr: str, dt: _dt.datetime) -> bool:
    return matches(parse_cron(expr), dt)


def next_run(spec_or_expr, after: _dt.datetime) -> _dt.datetime:
    """First datetime strictly after `after` matching the schedule.

    Brute-force minute stepping, capped at 366 days (impossible crons like
    Feb 30 raise ValueError instead of looping forever).
    """
    spec = parse_cron(spec_or_expr) if isinstance(spec_or_expr, str) else spec_or_expr
    cand = (after.replace(second=0, microsecond=0) + _dt.timedelta(minutes=1))
    for _ in range(366 * 24 * 60):
        if matches(spec, cand):
            return cand
        cand += _dt.timedelta(minutes=1)
    raise ValueError("no run in the next 366 days (impossible cron?)")


def _base(home: str | None) -> str:
    return home or _os.path.expanduser("~")


def sched_path(home: str | None = None) -> str:
    return _os.path.join(_base(home), ".tony", "schedule.json")


def ledger_path(home: str | None = None) -> str:
    return _os.path.join(_base(home), ".tony", "schedule-ledger.json")


def load(home: str | None = None) -> list:
    try:
        with open(sched_path(home)) as f:
            jobs = _json.load(f)
    except (OSError, ValueError):
        return []
    return jobs if isinstance(jobs, list) else []


def save(home: str | None, jobs: list) -> str:
    p = sched_path(home)
    _os.makedirs(_os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        _json.dump(jobs, f, indent=2)
    return p


def add(home: str | None, name: str, cron: str, mission: str) -> dict:
    """Append (or replace by name) a scheduled job. Validates the cron."""
    name = (name or "").strip()
    if not name:
        raise ValueError("schedule name must not be empty")
    parse_cron(cron)  # fail fast on bad cron, before touching disk
    if not (mission or "").strip():
        raise ValueError("schedule mission must not be empty")
    jobs = [j for j in load(home) if j.get("name") != name]
    job = {"name": name, "cron": cron.strip(), "mission": mission.strip()}
    jobs.append(job)
    save(home, jobs)
    return job


def remove(home: str | None, name: str) -> bool:
    jobs = load(home)
    kept = [j for j in jobs if j.get("name") != name]
    if len(kept) == len(jobs):
        return False
    save(home, kept)
    return True


def load_ledger(home: str | None = None) -> dict:
    try:
        with open(ledger_path(home)) as f:
            data = _json.load(f)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def minute_key(dt: _dt.datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M")


def scan_due(home: str | None = None, now: _dt.datetime | None = None) -> list:
    """Jobs whose cron matches the current minute and haven't fired it.

    Pure scan (no ledger writes): missed windows simply never appear again.
    """
    now = now or _dt.datetime.now()
    key = minute_key(now)
    ledger = load_ledger(home)
    due = []
    for job in load(home):
        try:
            spec = parse_cron(job.get("cron", ""))
        except ValueError:
            continue  # corrupt entry never fires, never blocks the scan
        if matches(spec, now) and ledger.get(job.get("name")) != key:
            due.append(job)
    return due


def mark_fired(home: str | None, name: str, now: _dt.datetime | None = None) -> None:
    now = now or _dt.datetime.now()
    p = ledger_path(home)
    _os.makedirs(_os.path.dirname(p), exist_ok=True)
    ledger = load_ledger(home)
    ledger[name] = minute_key(now)
    with open(p, "w") as f:
        _json.dump(ledger, f, indent=2)


def run_due(home: str | None, mission_fn, now: _dt.datetime | None = None) -> dict | None:
    """Execute the oldest due job. Empty/none-due -> None (noop)."""
    now = now or _dt.datetime.now()
    due = scan_due(home, now)
    if not due:
        return None
    job = due[0]
    try:
        report = mission_fn(job["mission"], "sched-" + job["name"])
        status = "ok"
    except Exception as e:  # one job's blowup never kills the daemon
        report = f"scheduled mission failed: {e}"
        status = "fail"
    mark_fired(home, job["name"], now)
    return {"name": "sched-" + job["name"], "status": status, "report": report}
