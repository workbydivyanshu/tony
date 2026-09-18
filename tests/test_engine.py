"""P3 RED proof: engine role_call + loop + demotion + runs.log must exist."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib import engine, boulder

def fake_ok(cmd, **kw):
    class R: returncode = 0; stdout = "DID THE THING\n"; stderr = ""
    return R()

def fake_fail_once():
    calls = {"n": 0}
    def run(cmd, **kw):
        calls["n"] += 1
        class R: pass
        r = R()
        if calls["n"] == 1:
            r.returncode = 1; r.stdout = ""; r.stderr = "429 busy"
        else:
            r.returncode = 0; r.stdout = "OK SECOND TRY\n"; r.stderr = ""
        return r
    return run

def test_role_call(tmpdir="/tmp/tony-test-eng"):
    os.makedirs(tmpdir, exist_ok=True)
    res = engine.role_call("builder", "opencode/big-pickle", "do X",
                           workdir=tmpdir, runner=fake_ok)
    assert res["status"] == "ok" and "DID THE THING" in res["output"], res
    assert os.path.exists(res["outfile"]), res

def test_loop_demote_then_ok(tmpdir="/tmp/tony-test-eng2"):
    os.makedirs(tmpdir, exist_ok=True)
    b = boulder.new("t")
    boulder.add_todo(b, "1. hard thing")
    engine.run_loop(b, {"builder": ["opencode/big-pickle", "opencode/mimo-v2.5-free"]},
                    workdir=tmpdir, runner=fake_fail_once(), runslog=os.path.join(tmpdir, "runs.log"))
    assert b["todos"][0]["box"] is True, b["todos"]
    rows = open(os.path.join(tmpdir, "runs.log")).read().strip().splitlines()
    assert len(rows) == 2 and "fail" in rows[0] and "ok" in rows[1], rows
