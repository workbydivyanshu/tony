"""P11 RED proof: cron scheduler (parse + store + due-scan + run_due) must exist."""
import datetime as dt
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib import sched


def _home():
    return tempfile.mkdtemp(prefix="tony-test-sched-")


def test_step_values():
    spec = sched.parse_cron("*/15 * * * *")
    assert spec["minute"] == {0, 15, 30, 45}, spec["minute"]


def test_range_and_list():
    spec = sched.parse_cron("0 9-11,14 * * *")
    assert spec["hour"] == {9, 10, 11, 14}, spec["hour"]


def test_dow_names():
    spec = sched.parse_cron("0 9 * * mon")
    monday = dt.datetime(2026, 9, 21, 9, 0)  # a Monday
    assert monday.weekday() == 0
    assert sched.matches(spec, monday)
    assert not sched.matches(spec, monday + dt.timedelta(days=1))
    assert not sched.matches(spec, monday + dt.timedelta(minutes=1))


def test_feb30_never_matches():
    # Feb 30 exists on no calendar: daily 02:30 scan over a leap year finds zero.
    spec = sched.parse_cron("30 2 30 2 *")
    day = dt.datetime(2024, 1, 1, 2, 30)
    hits = 0
    for _ in range(366):
        if sched.matches(spec, day):
            hits += 1
        day += dt.timedelta(days=1)
    assert hits == 0, hits
    try:
        sched.next_run(spec, dt.datetime(2024, 1, 1))
        assert False, "impossible cron must raise"
    except ValueError:
        pass


def test_next_run_daily():
    mon_8am = dt.datetime(2026, 9, 21, 8, 0)
    assert sched.next_run("0 9 * * *", mon_8am) == dt.datetime(2026, 9, 21, 9, 0)
    mon_10am = dt.datetime(2026, 9, 21, 10, 0)
    assert sched.next_run("0 9 * * *", mon_10am) == dt.datetime(2026, 9, 22, 9, 0)


def test_next_run_weekly():
    wed = dt.datetime(2026, 9, 23, 12, 0)  # Wednesday
    assert sched.next_run("0 0 * * sun", wed) == dt.datetime(2026, 9, 27, 0, 0)


def test_dom_dow_or_semantics():
    # 1st-of-month OR Sunday: both kinds of day fire, ordinary days don't.
    spec = sched.parse_cron("0 0 1 * sun")
    first_oct = dt.datetime(2026, 10, 1, 0, 0)  # Thursday, but the 1st
    assert sched.matches(spec, first_oct)
    assert sched.matches(spec, dt.datetime(2026, 9, 27, 0, 0))  # a Sunday
    assert not sched.matches(spec, dt.datetime(2026, 9, 23, 0, 0))  # Wed 23rd


def test_bad_cron_rejected():
    for bad in ("* * * *", "* * * * * *", "61 * * * *", "0 9 * * someday",
                "5-2 * * * *", "*/0 * * * *", ""):
        try:
            sched.parse_cron(bad)
            assert False, f"must reject: {bad!r}"
        except ValueError:
            pass


def test_store_roundtrip():
    home = _home()
    try:
        assert sched.load(home) == []
        job = sched.add(home, "morn", "0 9 * * *", "morning brief")
        assert job["name"] == "morn"
        jobs = sched.load(home)
        assert len(jobs) == 1 and jobs[0]["mission"] == "morning brief", jobs
        assert sched.remove(home, "morn") is True
        assert sched.load(home) == []
        assert sched.remove(home, "morn") is False
    finally:
        shutil.rmtree(home, ignore_errors=True)


def test_add_rejects_bad_cron_without_writing():
    home = _home()
    try:
        try:
            sched.add(home, "bad", "61 * * * *", "nope")
            assert False, "must reject"
        except ValueError:
            pass
        assert sched.load(home) == []
    finally:
        shutil.rmtree(home, ignore_errors=True)


def test_due_scan_fake_clock():
    home = _home()
    try:
        sched.add(home, "every", "* * * * *", "tick")
        now = dt.datetime(2026, 9, 18, 12, 0, 33)  # seconds ignored
        due = sched.scan_due(home, now)
        assert [j["name"] for j in due] == ["every"], due
        sched.mark_fired(home, "every", now)
        assert sched.scan_due(home, now) == []  # ledger guards the minute
        later = now + dt.timedelta(minutes=1)
        assert [j["name"] for j in sched.scan_due(home, later)] == ["every"]
        # missed window skipped: 9am job scanned at noon is NOT due
        sched.add(home, "nine", "0 9 * * *", "brief")
        assert all(j["name"] != "nine" for j in sched.scan_due(home, now))
    finally:
        shutil.rmtree(home, ignore_errors=True)


def test_run_due_executes_oldest_once():
    home = _home()
    try:
        sched.add(home, "every", "* * * * *", "tick tock")
        calls = []
        now = dt.datetime(2026, 9, 18, 12, 5)
        res = sched.run_due(home, lambda t, n: calls.append((t, n)) or "TICK", now)
        assert res is not None and res["status"] == "ok", res
        assert res["name"] == "sched-every", res
        assert calls == [("tick tock", "sched-every")], calls
        assert sched.run_due(home, lambda t, n: "never", now) is None
    finally:
        shutil.rmtree(home, ignore_errors=True)
