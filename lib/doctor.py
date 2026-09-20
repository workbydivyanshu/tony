"""doctor.py — tony --doctor self-diagnosis. Stdlib only.

Read-only probes, zero model calls. Every dependency is seam-injected so
tests run with fakes (temp HOME + lambdas); live bindings ride the real
lib modules. Honesty rule: absent-but-creatable paths are ok/skip detail,
never failures — a fresh machine is healthy, a half-initialized home is sick.
"""
import datetime as _dt
import json
import os
import re
import shutil
import subprocess

from lib import catalog, mcp, sched, tiers

Check = tuple  # (name, status, detail); status in {ok, warn, fail, skip}

_EXPECTED_ROLES = ("architect", "builder", "researcher",
                   "critic", "explorer", "scribe")


def _live_run(cmd: list) -> int:
    """Live run_fn binding: systemctl-style probe, int returncode."""
    return subprocess.run(cmd, capture_output=True, text=True,
                          timeout=30).returncode


def _read_json(path: str):
    """Return (ok, data|error-string). Never raises."""
    try:
        with open(path) as f:
            return True, json.load(f)
    except FileNotFoundError:
        return False, "missing"
    except (OSError, ValueError) as exc:
        return False, f"unreadable: {exc}"


def _check_binary(which_fn) -> Check:
    try:
        found = which_fn("opencode")
    except Exception as exc:
        return ("opencode_bin", "fail",
                f"binary lookup failed: {exc}; set $OPENCODE_BIN")
    if not found:
        return ("opencode_bin", "fail",
                "opencode binary not found on PATH; set $OPENCODE_BIN "
                "to its location")
    return ("opencode_bin", "ok", f"found at {found}")


def _check_catalog(catalog_fn) -> Check:
    try:
        models = catalog_fn()
    except Exception as exc:
        return ("catalog", "fail", f"catalog read failed: {exc}")
    if not models:
        return ("catalog", "ok", "catalog reachable, 0 models")
    return ("catalog", "ok", f"{len(models)} models")


def _home_config(home: str) -> dict:
    ok, data = _read_json(os.path.join(home, ".tony", "config.json"))
    if not ok or not isinstance(data, dict):
        return {}
    return data


def _check_roles(home: str) -> Check:
    if set(tiers.ROLES) != set(_EXPECTED_ROLES):
        return ("roles", "fail",
                f"role table drift: {sorted(tiers.ROLES)}")
    cfg = _home_config(home)
    overrides = cfg.get("roles", {}) or {}
    if not isinstance(overrides, dict):
        return ("roles", "ok",
                "6 roles on tier defaults (config roles malformed; "
                "see config check)")
    for role, pat in overrides.items():
        if role not in tiers.ROLES:
            return ("roles", "fail",
                    f"unknown role {role!r} in config")
        try:
            re.compile(pat)
        except re.error as exc:
            return ("roles", "fail",
                    f"role {role!r}: bad regex {exc}")
    return ("roles", "ok",
            f"6 roles defined, {len(overrides)} config overrides")


def _check_config(home: str) -> Check:
    ok, data = _read_json(os.path.join(home, ".tony", "config.json"))
    if not ok and data == "missing":
        return ("config", "ok", "no config.json; defaults active")
    if not ok:
        return ("config", "fail", f"config.json {data}")
    if not isinstance(data, dict):
        return ("config", "fail", "config.json is not an object")
    roles = data.get("roles", {})
    if not isinstance(roles, dict):
        return ("config", "fail", "config 'roles' is not an object")
    return ("config", "ok", f"config readable, {len(roles)} role overrides")


def _check_daemon(run_fn) -> Check:
    cmd = ["systemctl", "--user", "is-active", "tony-daemon.service"]
    try:
        res = run_fn(cmd)
    except FileNotFoundError:
        return ("daemon", "skip",
                "systemctl not found; daemon state unknown (never fake-PASS)")
    except Exception as exc:
        return ("daemon", "warn", f"daemon probe failed: {exc}")
    rc = res if isinstance(res, int) else getattr(res, "returncode", 0)
    if rc == 0:
        return ("daemon", "ok", "tony-daemon.service active")
    return ("daemon", "warn",
            "tony-daemon.service inactive; start with "
            "`systemctl --user start tony-daemon.service` "
            "(or --install-daemon if never installed)")


def _check_schedules(home: str) -> Check:
    tdir = os.path.join(home, ".tony")
    try:
        if not os.path.isdir(tdir):
            return ("schedules", "skip",
                    "no ~/.tony yet (fresh machine); "
                    "schedules install with --install-defaults")
        ok, jobs = _read_json(sched.sched_path(home))
    except OSError as exc:
        return ("schedules", "fail", f"schedule store not accessible: {exc}")
    if not ok:
        if jobs == "missing":
            return ("schedules", "fail",
                    "schedule.json absent in initialized ~/.tony; "
                    "morning-briefing/memory-hygiene never fire — "
                    "run --install-defaults")
        return ("schedules", "fail", f"schedule.json {jobs}")
    if not isinstance(jobs, list):
        return ("schedules", "fail", "schedule.json is not a list")
    now = _dt.datetime.now()
    for job in jobs:
        if not isinstance(job, dict):
            return ("schedules", "fail", f"schedule entry not an object: {job!r}")
        name = job.get("name") or "<unnamed>"
        for field in ("name", "cron", "mission"):
            if not (job.get(field) or "").strip():
                return ("schedules", "fail",
                        f"job {name!r}: missing {field}")
        try:
            sched.next_run(job["cron"], now)
        except ValueError as exc:
            return ("schedules", "fail",
                    f"job {name!r}: bad cron {job['cron']!r} ({exc})")
    return ("schedules", "ok", f"{len(jobs)} jobs")


def _check_ledger(home: str) -> Check:
    ok, data = _read_json(sched.ledger_path(home))
    if not ok and data == "missing":
        return ("ledger", "ok",
                "no schedule-ledger.json yet (no job fired)")
    if not ok:
        return ("ledger", "warn", f"schedule-ledger.json corrupt: {data}")
    if not isinstance(data, dict):
        return ("ledger", "warn",
                "schedule-ledger.json is not an object; ledger ignored")
    return ("ledger", "ok", f"{len(data)} ledger entries")


def _check_home(home: str) -> Check:
    try:
        accessible = os.access(home, os.W_OK | os.X_OK)
        tdir = os.path.join(home, ".tony")
        tdir_exists = os.path.isdir(tdir)
    except OSError as exc:
        return ("home", "fail", f"home not accessible: {exc}")
    if not accessible:
        return ("home", "fail", f"home {home} not writable")
    if not tdir_exists:
        return ("home", "ok",
                "~/.tony absent but parent writable; created on first run")
    try:
        if not os.access(tdir, os.W_OK):
            return ("home", "fail", f"{tdir} present but not writable")
    except OSError as exc:
        return ("home", "fail", f"{tdir} not accessible: {exc}")
    return ("home", "ok", f"{tdir} writable")


def _check_mcp(mcp_fn) -> Check:
    try:
        names = mcp_fn()
    except Exception as exc:
        return ("mcp", "warn", f"mcp probe failed: {exc}")
    if not names:
        return ("mcp", "ok",
                "no MCP servers connected; delegates run without tools")
    return ("mcp", "ok",
            f"{len(names)} servers: {', '.join(names)}")


def run_all(home=None, catalog_fn=None, mcp_fn=None,
            run_fn=None, which_fn=None) -> list:
    """Run all checks -> [(name, status, detail)]. Never raises for
    check-level failures (each check guards its own seam); never burns
    model calls; never mutates disk."""
    home = home or os.path.expanduser("~")
    if catalog_fn is None:
        catalog_fn = catalog.live_catalog
    if mcp_fn is None:
        mcp_fn = mcp.names
    if run_fn is None:
        run_fn = _live_run
    if which_fn is None:
        which_fn = shutil.which
    return [
        _check_binary(which_fn),
        _check_catalog(catalog_fn),
        _check_roles(home),
        _check_config(home),
        _check_daemon(run_fn),
        _check_schedules(home),
        _check_ledger(home),
        _check_home(home),
        _check_mcp(mcp_fn),
    ]
