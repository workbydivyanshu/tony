"""P25 claim-race guard: loser must yield, loop must survive stolen claim, winner must still run."""
import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib import daemon


def _home():
    d = tempfile.mkdtemp(prefix="tony-test-claim-race-")
    return d


def test_loser_yields_none():
    home = _home()
    try:
        inbox = daemon.inbox_dir(home)
        os.makedirs(inbox, exist_ok=True)
        with open(os.path.join(inbox, "job.md"), "w") as f:
            f.write("do the thing")
        calls = []

        def fake_mission(text, name):
            calls.append((text, name))
            return "REPORT OK"

        # Simulate the lost race synchronously: peer removes src in the
        # TOCTOU window between run_once's internal list_pending and claim.
        # (Pre-claiming to job.md.claimed would NOT test this — list_pending
        # skips .claimed files, so run_once would noop vacuously.)
        real_claim = daemon.claim

        def racy_claim(path):
            os.remove(path)  # peer won between list and claim
            return real_claim(path)  # raises FileNotFoundError

        daemon.claim = racy_claim
        try:
            res = daemon.run_once(inbox, fake_mission, home=home)
        finally:
            daemon.claim = real_claim
        assert res is None, res
        assert calls == [], calls
        done = os.path.join(daemon.done_dir(home), "job.done.md")
        assert not os.path.exists(done), done
        assert daemon.list_pending(inbox) == [], daemon.list_pending(inbox)
    finally:
        shutil.rmtree(home, ignore_errors=True)


def test_loop_survives_stolen_claim():
    home = _home()
    try:
        inbox = daemon.inbox_dir(home)
        os.makedirs(inbox, exist_ok=True)
        with open(os.path.join(inbox, "job.md"), "w") as f:
            f.write("job")

        # Same lost-race injection as S1, driven through the resident loop.
        real_claim = daemon.claim

        def racy_claim(path):
            os.remove(path)  # peer won between list and claim
            return real_claim(path)  # raises FileNotFoundError

        def _sleep(s):
            raise KeyboardInterrupt

        daemon.claim = racy_claim
        try:
            n = daemon.loop(inbox, lambda t, name: "x", interval=0,
                            stop_after=1, sleep_fn=_sleep, home=home)
        finally:
            daemon.claim = real_claim
        assert n == 0, n
    finally:
        shutil.rmtree(home, ignore_errors=True)


def test_winner_still_runs():
    home = _home()
    try:
        inbox = daemon.inbox_dir(home)
        os.makedirs(inbox, exist_ok=True)
        with open(os.path.join(inbox, "job.md"), "w") as f:
            f.write("do the thing")
        calls = []

        def fake_mission(text, name):
            calls.append((text, name))
            return "REPORT OK"

        res = daemon.run_once(inbox, fake_mission, home=home)
        assert res is not None and res["status"] == "ok", res
        assert calls == [("do the thing", "job")], calls
        done = os.path.join(daemon.done_dir(home), "job.done.md")
        assert os.path.exists(done), done
        assert "# job — ok\n\nREPORT OK\n" in open(done).read()
        assert daemon.list_pending(inbox) == [], daemon.list_pending(inbox)
    finally:
        shutil.rmtree(home, ignore_errors=True)
