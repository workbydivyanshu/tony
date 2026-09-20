"""tests/test_p17.py — P17 RED: role timeout budgets + short backoff."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_budgets_exist():
    from lib import engine
    assert engine.role_timeout("architect", 600) == 600
    assert engine.role_timeout("explorer", 600) == 240
    assert engine.role_timeout("scribe", 600) == 120
    assert engine.role_timeout("builder", 600) == 480
    assert engine.role_timeout("mystery", 600) == 600


def test_backoff_short():
    from lib import engine
    assert engine.BACKOFF_SECS == (5, 10), engine.BACKOFF_SECS
    assert engine.MAX_BACKOFF_ATTEMPTS == 2, engine.MAX_BACKOFF_ATTEMPTS


def test_exec_applies_budget():
    from lib import engine
    seen = {}
    def fake_run(cmd, **kw):
        seen["cmd"] = cmd
        seen["timeout"] = kw.get("timeout")
        class P: returncode = 0; stdout = "ok"; stderr = ""
        return P()
    import tempfile, shutil
    d = tempfile.mkdtemp(); os.makedirs(os.path.join(d, "work"), exist_ok=True)
    from lib import boulder
    b = boulder.new("t")
    boulder.add_todo(b, "[role:explorer] find things")
    engine._exec_one(b, 0, {"explorer": ["opencode/m"]}, os.path.join(d, "work"),
                     runner=fake_run, runslog=os.path.join(d, "runs.log"),
                     sleep_fn=None, timeout=600)
    assert seen["timeout"] == 240, seen
    shutil.rmtree(d, ignore_errors=True)


def test_demote_applies_budget():
    from lib import engine
    seen = []

    def fake_run(cmd, **kw):
        seen.append(kw.get("timeout"))
        class P: returncode = 1; stdout = ""; stderr = "boom"
        return P()
    import tempfile, shutil
    d = tempfile.mkdtemp(); os.makedirs(os.path.join(d, "work"), exist_ok=True)
    from lib import boulder
    b = boulder.new("t")
    boulder.add_todo(b, "[role:explorer] hard thing")
    engine._exec_one(b, 0, {"explorer": ["m1", "m2"]}, os.path.join(d, "work"),
                     runner=fake_run, runslog=os.path.join(d, "runs.log"),
                     sleep_fn=None, timeout=600)
    assert seen == [240, 240], seen  # primary + demote both capped
    assert b["todos"][0]["text"].endswith("[BLOCKED]")
    shutil.rmtree(d, ignore_errors=True)


def test_effective_timeout_fast():
    from lib import engine
    assert engine.effective_timeout(600, False) == 600
    assert engine.effective_timeout(600, True) == 300
    assert engine.effective_timeout(90, True) == 60  # floor holds
    # fast mission still scales per-role: explorer 0.4 * 300 = 120
    assert engine.role_timeout("explorer", engine.effective_timeout(600, True)) == 120