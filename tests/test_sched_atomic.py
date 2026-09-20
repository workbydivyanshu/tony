"""P26 atomic-write proof: save/mark_fired must survive mid-write json.dump failure.

Fault injection = monkeypatch sched._json.dump to raise mid-write.
Pre-fix: S1+S2 FAIL (file truncated -> load returns [] / {}).
Pre-fix: S3+S4 PASS (no tmp residue + normal roundtrip).
"""
import datetime as dt
import glob
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib import sched


def _home():
    return tempfile.mkdtemp(prefix="tony-test-sched-")


def _faulty_dump(*args, **kwargs):
    raise RuntimeError("injected fault: json.dump raised mid-write")


def test_interrupted_save_keeps_prior_jobs():
    home = _home()
    try:
        # Seed 2 jobs via sched.add
        j1 = sched.add(home, "alpha", "* * * * *", "mission alpha")
        j2 = sched.add(home, "beta", "0 9 * * *", "mission beta")
        assert len(sched.load(home)) == 2, sched.load(home)

        # Patch json.dump in sched module namespace to raise mid-write
        orig_dump = sched._json.dump
        sched._json.dump = _faulty_dump
        try:
            # save(home, jobs) must raise
            try:
                sched.save(home, [j1, j2])
                assert False, "save must raise under fault injection"
            except RuntimeError:
                pass
            # Pre-fix RED: file truncated -> load returns []
            # Post-fix: prior jobs preserved
            result = sched.load(home)
            assert len(result) == 2, f"expected 2 prior jobs, got {result}"
            assert {j["name"] for j in result} == {"alpha", "beta"}
        finally:
            sched._json.dump = orig_dump
    finally:
        shutil.rmtree(home, ignore_errors=True)


def test_interrupted_mark_keeps_prior_ledger():
    home = _home()
    try:
        # Seed ledger via mark_fired
        now = dt.datetime(2026, 9, 18, 12, 0)
        sched.mark_fired(home, "alpha", now)
        ledger = sched.load_ledger(home)
        assert ledger.get("alpha") == sched.minute_key(now), ledger

        # Patch json.dump in sched module namespace to raise mid-write
        orig_dump = sched._json.dump
        sched._json.dump = _faulty_dump
        try:
            # mark_fired must raise
            try:
                sched.mark_fired(home, "alpha", now + dt.timedelta(minutes=1))
                assert False, "mark_fired must raise under fault injection"
            except RuntimeError:
                pass
            # Pre-fix RED: torn ledger -> {}
            # Post-fix: prior entry preserved
            result = sched.load_ledger(home)
            assert "alpha" in result, f"expected prior ledger entry, got {result}"
            assert result["alpha"] == sched.minute_key(now)
        finally:
            sched._json.dump = orig_dump
    finally:
        shutil.rmtree(home, ignore_errors=True)


def test_no_tmp_residue():
    home = _home()
    try:
        # Successful save + mark_fired must leave zero *.tmp files
        sched.add(home, "gamma", "* * * * *", "mission gamma")
        now = dt.datetime(2026, 9, 18, 12, 0)
        sched.mark_fired(home, "gamma", now)
        tmp_files = glob.glob(os.path.join(home, "**", "*.tmp"), recursive=True)
        assert tmp_files == [], f"unexpected tmp residue: {tmp_files}"
    finally:
        shutil.rmtree(home, ignore_errors=True)


def test_save_mark_roundtrip():
    home = _home()
    try:
        # Normal add/save/load round-trip
        job = sched.add(home, "delta", "0 9 * * *", "morning brief")
        assert job["name"] == "delta"
        jobs = sched.load(home)
        assert len(jobs) == 1 and jobs[0]["mission"] == "morning brief"

        # Normal mark_fired/load_ledger round-trip
        now = dt.datetime(2026, 9, 18, 9, 0)
        sched.mark_fired(home, "delta", now)
        ledger = sched.load_ledger(home)
        assert ledger["delta"] == sched.minute_key(now)
    finally:
        shutil.rmtree(home, ignore_errors=True)
