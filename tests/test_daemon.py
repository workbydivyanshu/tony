"""P10 RED proof: inbox daemon (claim + run-once + empty-noop) must exist."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib import daemon


def _home():
    d = tempfile.mkdtemp(prefix="tony-test-daemon-")
    return d


def test_list_and_claim():
    home = _home()
    inbox = daemon.inbox_dir(home)
    os.makedirs(inbox, exist_ok=True)
    with open(os.path.join(inbox, "a.md"), "w") as f:
        f.write("mission A")
    pending = daemon.list_pending(inbox)
    assert pending == [os.path.join(inbox, "a.md")], pending
    claimed = daemon.claim(pending[0])
    assert claimed.endswith(".claimed")
    assert daemon.list_pending(inbox) == []


def test_run_once_executes():
    import shutil
    home = _home()
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
    assert "REPORT OK" in open(done).read()
    assert daemon.list_pending(inbox) == []
    shutil.rmtree(home, ignore_errors=True)


def test_run_once_empty_noop():
    import shutil
    home = _home()
    inbox = daemon.inbox_dir(home)
    os.makedirs(inbox, exist_ok=True)
    calls = []
    res = daemon.run_once(inbox, lambda t, n: calls.append((t, n)) or "x", home=home)
    assert res is None, res
    assert calls == []
    shutil.rmtree(home, ignore_errors=True)


def test_loop_runs_one_then_stops():
    import shutil
    home = _home()
    inbox = daemon.inbox_dir(home)
    os.makedirs(inbox, exist_ok=True)
    with open(os.path.join(inbox, "j.md"), "w") as f:
        f.write("job")
    n = daemon.loop(inbox, lambda t, name: "ok", interval=0,
                    stop_after=1, sleep_fn=lambda s: None, home=home)
    assert n == 1, n
    shutil.rmtree(home, ignore_errors=True)


def test_loop_keyboard_interrupt_exits():
    import shutil
    home = _home()
    inbox = daemon.inbox_dir(home)
    os.makedirs(inbox, exist_ok=True)

    def _sleep(s):
        raise KeyboardInterrupt

    n = daemon.loop(inbox, lambda t, name: "x", interval=0,
                    sleep_fn=_sleep, home=home)
    assert n == 0, n
    shutil.rmtree(home, ignore_errors=True)


def test_read_fail_releases_claim():
    # read-fail must un-claim: claimed files are invisible to list_pending,
    # so leaving them claimed would wedge the mission forever.
    import shutil
    home = _home()
    inbox = daemon.inbox_dir(home)
    os.makedirs(inbox, exist_ok=True)
    p = os.path.join(inbox, "locked.md")
    with open(p, "w") as f:
        f.write("secret")
    os.chmod(p, 0)
    try:
        res = daemon.run_once(inbox, lambda t, name: "never", home=home)
        assert res is not None and res["status"].startswith("read-fail"), res
        assert daemon.list_pending(inbox) == [p], daemon.list_pending(inbox)
    finally:
        os.chmod(p, 0o600)
        shutil.rmtree(home, ignore_errors=True)
