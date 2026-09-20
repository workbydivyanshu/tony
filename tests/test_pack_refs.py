"""tests/test_pack_refs.py — P27 pack-ref validation in _check_schedules.

S1: missing pack -> warn naming job + pack.
S2: present pack -> no pack-related warn.
S3: bad cron -> still fails (regression anchor).
S4: two refs, one missing -> warn names only the missing one.

Pre-fix RED: _check_schedules is blind to @pack: refs — it never
consults packs.py, so S1/S4 fail (no warn emitted) and S2/S3 pass.

Detection mechanism mirrored from lib/packs.py:
  _PACK_RE = re.compile(r"@pack:([A-Za-z0-9][A-Za-z0-9_-]*)")
Home-scoping mirrored from lib/doctor.py _check_schedules(home):
  schedule.json at home/.tony/schedule.json, packs at home/.tony/packs/.
"""
import json
import os
import re
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import lib.doctor  # noqa: F401

# Mirror production ref-detection regex exactly (lib/packs.py _PACK_RE).
_PACK_RE = re.compile(r"@pack:([A-Za-z0-9][A-Za-z0-9_-]*)")


def _write_schedule(home, jobs):
    """Write schedule.json under tmp home."""
    tdir = os.path.join(home, ".tony")
    os.makedirs(tdir, exist_ok=True)
    with open(os.path.join(tdir, "schedule.json"), "w") as f:
        json.dump(jobs, f)


def _write_pack(home, name, body="pack content"):
    """Write a pack file under tmp home packs dir."""
    pd = os.path.join(home, ".tony", "packs")
    os.makedirs(pd, exist_ok=True)
    with open(os.path.join(pd, name + ".md"), "w") as f:
        f.write(body)


def test_missing_pack_warns():
    """S1: schedule.json job with @pack:ghostpack (no packs dir) ->
    _check_schedules returns ('schedules', 'warn', detail) where detail
    names both the job 'myjob' and the pack 'ghostpack'.

    Pre-fix RED: _check_schedules never consults packs, so it returns
    ('schedules', 'ok', '1 jobs') — no warn at all. The warn is absent
    because the check never looks at packs (not because the test setup
    is invisible to the check). Confirmed mechanism: _check_schedules
    validates cron and required fields only; it has no code path that
    calls packs.read_pack, packs.expand, or packs.has_pack_ref.
    """
    home = tempfile.mkdtemp(prefix="tony-pack-refs-")
    try:
        _write_schedule(home, [
            {"name": "myjob", "cron": "* * * * *",
             "mission": "@pack:ghostpack"}
        ])
        result = lib.doctor._check_schedules(home)
        assert result[0] == "schedules"
        assert result[1] == "warn", (
            f"PRE-FIX RED confirmed: got {result!r} — "
            f"_check_schedules is blind to @pack: refs; "
            f"it never calls packs.read_pack/expand/has_pack_ref"
        )
        assert "myjob" in result[2], f"detail must name job: {result[2]!r}"
        assert "ghostpack" in result[2], f"detail must name pack: {result[2]!r}"
    finally:
        shutil.rmtree(home)


def test_present_pack_no_warn():
    """S2: same setup but pack file EXISTS under tmp home packs dir ->
    no pack-related warn. Proves the check resolves rather than always
    firing (a warn-on-every-job check would fire here too).

    Pre-fix: _check_schedules returns ('schedules', 'ok', '1 jobs') —
    no warn at all, so the assertion passes. This confirms the check
    is not unconditionally firing warns; it simply doesn't look at
    packs yet.
    """
    home = tempfile.mkdtemp(prefix="tony-pack-refs-")
    try:
        _write_schedule(home, [
            {"name": "myjob", "cron": "* * * * *",
             "mission": "@pack:realpack"}
        ])
        _write_pack(home, "realpack")
        result = lib.doctor._check_schedules(home)
        # No pack-related warn: either ok (pre-fix) or warn without
        # this pack name (post-fix with present pack).
        assert not (result[1] == "warn" and "realpack" in result[2]), (
            f"present pack must not produce pack warn: {result!r}"
        )
    finally:
        shutil.rmtree(home)


def test_bad_cron_still_fails():
    """S3: bad cron -> _check_schedules returns ('schedules', 'fail',
    detail naming the job and 'cron'). Regression anchor: this
    existing behavior must be unaffected by the pack-ref check.

    Pre-fix: PASS — bad-cron validation already exists in _check_schedules
    (line: sched.next_run(job['cron'], now) raises ValueError).
    """
    home = tempfile.mkdtemp(prefix="tony-pack-refs-")
    try:
        _write_schedule(home, [
            {"name": "badjob", "cron": "not-a-cron",
             "mission": "do work"}
        ])
        result = lib.doctor._check_schedules(home)
        assert result[1] == "fail", f"bad cron must fail: {result!r}"
        assert "badjob" in result[2], f"detail must name job: {result[2]!r}"
        assert "cron" in result[2].lower(), f"detail must mention cron: {result[2]!r}"
    finally:
        shutil.rmtree(home)


def test_two_refs_one_missing_warns_only_missing():
    """S4: mission with two @pack: refs, one missing -> warn names
    only the missing pack, not the present one.

    Pre-fix RED: _check_schedules is blind to all pack refs, returns
    ('schedules', 'ok', '1 jobs'). The warn is absent because the
    check never iterates @pack: matches at all.

    Only included because sched.run_due expansion (lib/packs.py
    _PACK_RE.sub) supports multiple refs per mission text.
    """
    home = tempfile.mkdtemp(prefix="tony-pack-refs-")
    try:
        _write_schedule(home, [
            {"name": "multijob", "cron": "* * * * *",
             "mission": "@pack:missingpack @pack:presentpack"}
        ])
        _write_pack(home, "presentpack")
        # Verify the mission text actually contains two refs
        mission = [j["mission"] for j in json.loads(
            open(os.path.join(home, ".tony", "schedule.json")).read()
        )][0]
        refs = _PACK_RE.findall(mission)
        assert len(refs) == 2, f"mission must have 2 refs: {refs}"
        assert "missingpack" in refs and "presentpack" in refs

        result = lib.doctor._check_schedules(home)
        assert result[1] == "warn", (
            f"PRE-FIX RED: got {result!r} — _check_schedules never "
            f"scans @pack: matches"
        )
        assert "missingpack" in result[2], (
            f"warn must name missing pack: {result[2]!r}"
        )
        assert "presentpack" not in result[2], (
            f"warn must NOT name present pack: {result[2]!r}"
        )
    finally:
        shutil.rmtree(home)
