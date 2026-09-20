"""P5a RED proof: role tags + parallel explorers + max-verify must exist."""
import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib import engine, boulder


def test_role_tag_parse():
    assert engine.todo_role("[role:explorer] recon auth flow") == "explorer"
    assert engine.todo_role("1. hard thing") == "builder"
    assert engine.todo_role("[role:researcher] dig papers") == "researcher"


def _slow_ok(cmd, **kw):
    time.sleep(0.6)
    class R: returncode = 0; stdout = "OK\n"; stderr = ""
    return R()


def test_parallel_explorers_overlap(tmpdir="/tmp/tony-test-p5par"):
    # e2e-burn unjustified for threading: fake-runner overlap at the seam is the proof.
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)
    os.makedirs(tmpdir, exist_ok=True)
    b = boulder.new("t")
    boulder.add_todo(b, "[role:explorer] recon A")
    boulder.add_todo(b, "[role:explorer] recon B")
    t0 = time.time()
    engine.run_loop(b, {"explorer": ["opencode/mimo-v2.5-free"]},
                    workdir=tmpdir, runner=_slow_ok,
                    runslog=os.path.join(tmpdir, "runs.log"), parallel=True)
    wall = time.time() - t0
    assert all(t["box"] for t in b["todos"]), b["todos"]
    assert wall < 1.0, f"no overlap: {wall:.2f}s"
    rows = open(os.path.join(tmpdir, "runs.log")).read().strip().splitlines()
    assert len(rows) == 2 and all("ok" in r for r in rows), rows
    shutil.rmtree(tmpdir, ignore_errors=True)


def test_builders_stay_sequential(tmpdir="/tmp/tony-test-p5seq"):
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)
    os.makedirs(tmpdir, exist_ok=True)
    b = boulder.new("t")
    boulder.add_todo(b, "1. build A")
    boulder.add_todo(b, "2. build B")
    t0 = time.time()
    engine.run_loop(b, {"builder": ["opencode/big-pickle"]},
                    workdir=tmpdir, runner=_slow_ok,
                    runslog=os.path.join(tmpdir, "runs.log"), parallel=True)
    wall = time.time() - t0
    assert all(t["box"] for t in b["todos"]), b["todos"]
    assert wall >= 1.0, f"builders must stay sequential: {wall:.2f}s"
    shutil.rmtree(tmpdir, ignore_errors=True)


def test_verify_wave_max_verify(tmpdir="/tmp/tony-test-p5wave"):
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)
    os.makedirs(tmpdir, exist_ok=True)
    b = boulder.new("t")
    boulder.add_wave(b, "false")
    calls = {"n": 0}
    res = engine.verify_wave(b, max_verify=2, cwd=tmpdir,
                             fix_fn=lambda fails: calls.__setitem__("n", calls["n"] + 1))
    # gated: fix runs between attempts only, never after the final one (note 3)
    assert res == [False] and calls["n"] == 1, (res, calls)
    shutil.rmtree(tmpdir, ignore_errors=True)
