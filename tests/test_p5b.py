"""P5b RED proof: review-notes hardening (notes 1-5, 8)."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib import engine, boulder


def test_resolve_role_shared_precedence():
    # explicit role wins; tag fallback; untagged -> builder (note 1)
    assert engine.resolve_role({"text": "[role:explorer] recon", "role": "builder"}) == "builder"
    assert engine.resolve_role({"text": "[role:explorer] recon"}) == "explorer"
    assert engine.resolve_role({"text": "1. plain build"}) == "builder"
    assert engine.resolve_role({"text": "[role:researcher] dig"}) == "researcher"


def test_unknown_tag_logs_fallback_once():
    # unknown tag -> builder WITH exactly one visible log line (note 2)
    b = boulder.new("t")
    boulder.add_todo(b, "[role:explorrer] typo recon")
    assert engine.resolve_role(b["todos"][0], b) == "builder"
    hits = [l for l in b["log"] if "explorrer" in l]
    assert len(hits) == 1 and "builder" in hits[0], b["log"]


def test_verify_wave_gates_last_fix_and_none_log(tmpdir="/tmp/tony-test-p5b-wave"):
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)
    os.makedirs(tmpdir, exist_ok=True)
    # max_verify=3 always-fail -> fix runs between attempts only = 2 calls (note 3)
    b = boulder.new("t")
    boulder.add_wave(b, "false")
    calls = {"n": 0}
    res = engine.verify_wave(b, max_verify=3, cwd=tmpdir,
                             fix_fn=lambda fails: calls.__setitem__("n", calls["n"] + 1))
    assert res == [False] and calls["n"] == 2, (res, calls)
    assert any("exhausted (3 attempts)" in l for l in b["log"]), b["log"]
    # fix_fn=None -> honest log, no crash, wave still re-runs (note 4)
    b2 = boulder.new("t")
    boulder.add_wave(b2, "false")
    res2 = engine.verify_wave(b2, max_verify=2, cwd=tmpdir, fix_fn=None)
    assert res2 == [False]
    assert any("no fix_fn" in l for l in b2["log"]), b2["log"]
    assert not any("feeding fix" in l for l in b2["log"]), b2["log"]
    shutil.rmtree(tmpdir, ignore_errors=True)


def test_exec_one_contains_fs_blowup(tmpdir="/tmp/tony-test-p5b-fs"):
    # workdir is a FILE -> makedirs raises; TODO contained as [BLOCKED], no raise (note 5)
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)
    os.makedirs(tmpdir, exist_ok=True)
    blockfile = os.path.join(tmpdir, "not-a-dir")
    open(blockfile, "w").write("x")
    b = boulder.new("t")
    boulder.add_todo(b, "1. build thing")
    engine._exec_one(b, 0, {"builder": ["opencode/big-pickle"]}, blockfile,
                     runner=lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not run")),
                     runslog=os.path.join(tmpdir, "runs.log"))
    assert "[BLOCKED]" in b["todos"][0]["text"], b["todos"][0]
    assert any("BLOCKED (exception" in l for l in b["log"]), b["log"]
    shutil.rmtree(tmpdir, ignore_errors=True)


def test_run_loop_no_dead_param():
    # now_stamp removed from the signature (note 8)
    import inspect
    assert "now_stamp" not in inspect.signature(engine.run_loop).parameters
