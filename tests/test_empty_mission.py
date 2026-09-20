"""tests/test_empty_mission.py — T1 self-trial: run_due must not dispatch
an empty expanded mission to the model (burns a call on nothing, then
marks fired as if work happened). Ghost-pack missions expand to "".
"""
import datetime as dt
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib import sched


def _home():
    return tempfile.mkdtemp(prefix="tony-test-empty-mission-")


_NOW = dt.datetime(2026, 9, 21, 7, 31)


def test_ghost_pack_skips_without_dispatch():
    """@pack:ghostpack (no packs dir) -> skipped-empty-mission, fn uncalled,
    ledger marked so an immediate second run_due is None (no storm)."""
    home = _home()
    try:
        sched.add(home, "ghosty", "* * * * *", "@pack:ghostpack")
        calls = []
        res = sched.run_due(
            home, lambda t, n: calls.append((t, n)) or "NEVER", _NOW)
        assert res is not None, "due job must produce a record, not None"
        assert res["status"] == "skipped-empty-mission", res
        assert calls == [], calls
        assert sched.run_due(home, lambda t, n: "never", _NOW) is None
    finally:
        shutil.rmtree(home, ignore_errors=True)


def test_normal_mission_still_dispatches():
    """Real mission text -> ok anchor (passes pre- and post-fix)."""
    home = _home()
    try:
        sched.add(home, "every", "* * * * *", "tick tock")
        calls = []
        res = sched.run_due(
            home, lambda t, n: calls.append((t, n)) or "TICK", _NOW)
        assert res is not None and res["status"] == "ok", res
        assert calls == [("tick tock", "sched-every")], calls
    finally:
        shutil.rmtree(home, ignore_errors=True)


def test_double_missing_pack_skips():
    """Two missing refs expand to whitespace -> same skip, fn uncalled."""
    home = _home()
    try:
        sched.add(home, "doubly", "* * * * *",
                  "@pack:missing @pack:alsomissing")
        calls = []
        res = sched.run_due(
            home, lambda t, n: calls.append((t, n)) or "NEVER", _NOW)
        assert res is not None, "due job must produce a record, not None"
        assert res["status"] == "skipped-empty-mission", res
        assert calls == [], calls
    finally:
        shutil.rmtree(home, ignore_errors=True)
