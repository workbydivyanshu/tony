"""tests/test_sched_done_report.py — P36: sched-branch done-file+notify.

run_once's SCHED branch must mirror the inbox path artifacts (done-file
+ notify). Fakes only: fake mission_fn, monkeypatched daemon.notify,
tmp HOME dirs. Zero model burn, zero sleep, zero real-HOME mutation.
"""
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib import daemon, sched


def _run(homesetup, mission_fn):
    """Run run_once on a tmp HOME. Returns (res, notified, home, calls)."""
    home = tempfile.mkdtemp(prefix="tony-test-sched-done-")
    notified = []
    calls = []
    real_notify = daemon.notify
    daemon.notify = lambda t, b: notified.append((t, b))

    def wrapped(text, name):
        calls.append((text, name))
        return mission_fn(text, name)

    try:
        homesetup(home)
        res = daemon.run_once(daemon.inbox_dir(home), wrapped, home=home)
        return res, notified, home, calls
    finally:
        daemon.notify = real_notify


def _clean(home):
    shutil.rmtree(home, ignore_errors=True)


def _seed_ok(home):
    os.makedirs(daemon.inbox_dir(home), exist_ok=True)
    sched.add(home, "dawn", "* * * * *", "do X")


def test_sched_ok_writes_donefile_and_notifies():
    """Due job ok -> done-file with report + notify(title, body)."""
    res, notified, home, calls = _run(_seed_ok, lambda t, n: "REPORT")
    try:
        assert res is not None and res["status"] == "ok", res
        p = os.path.join(daemon.done_dir(home), "sched-dawn.done.md")
        assert os.path.isfile(p), p
        body = open(p).read()
        assert "# sched-dawn — ok" in body, body
        assert "REPORT" in body, body
        assert notified == [("tony: sched-dawn",
                             f"mission ok — report: {p}")], notified
        assert calls == [("do X", "sched-dawn")], calls
    finally:
        _clean(home)


def test_sched_fail_writes_donefile_and_notifies():
    """Raising mission -> fail record + failure text + notify."""
    def boom(text, name):
        raise RuntimeError("boom")

    res, notified, home, calls = _run(_seed_ok, boom)
    try:
        assert res is not None and res["status"] == "fail", res
        p = os.path.join(daemon.done_dir(home), "sched-dawn.done.md")
        assert os.path.isfile(p), p
        assert "scheduled mission failed: boom" in open(p).read()
        assert len(notified) == 1 and "fail" in notified[0][1], notified
    finally:
        _clean(home)


def test_skipped_empty_mission_files_and_notifies():
    """Ghost-pack mission -> skipped record, model never called."""
    def setup(home):
        os.makedirs(daemon.inbox_dir(home), exist_ok=True)
        sched.add(home, "ghosty", "* * * * *", "@pack:ghostpack")

    res, notified, home, calls = _run(setup, lambda t, n: "NEVER")
    try:
        assert res is not None, res
        assert res["status"] == "skipped-empty-mission", res
        assert calls == [], calls
        p = os.path.join(daemon.done_dir(home), "sched-ghosty.done.md")
        assert os.path.isfile(p), p
        assert len(notified) == 1, notified
    finally:
        _clean(home)


def test_nothing_due_writes_nothing():
    """No jobs -> None, no files, no notify, mission_fn uncalled."""
    def setup(home):
        os.makedirs(daemon.inbox_dir(home), exist_ok=True)

    res, notified, home, calls = _run(setup, lambda t, n: "NEVER")
    try:
        assert res is None, res
        assert calls == [], calls
        assert notified == [], notified
        assert not os.path.exists(daemon.done_dir(home)) or \
            os.listdir(daemon.done_dir(home)) == [], daemon.done_dir(home)
    finally:
        _clean(home)
