"""P5c-1 RED proof: --resume continuity + --keep-going wave gating."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib import engine, boulder


def _fake_ok_recorder(seen):
    def run(cmd, **kw):
        seen.append(cmd[-1] if isinstance(cmd, list) else cmd)
        class P: returncode = 0; stdout = "ok"; stderr = ""
        return P()
    return run


def test_resume_skips_done(tmpdir="/tmp/tony-test-p5c-resume"):
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)
    os.makedirs(tmpdir, exist_ok=True)
    b = boulder.new("resume-t")
    boulder.add_todo(b, "1. done already", done=True)
    boulder.add_todo(b, "2. still open")
    seen = []
    engine.run_loop(b, {"builder": ["opencode/big-pickle"]}, tmpdir,
                    runner=_fake_ok_recorder(seen),
                    runslog=os.path.join(tmpdir, "runs.log"))
    assert len(seen) == 1 and "still open" in seen[0], seen
    assert b["todos"][0]["box"] is True and b["todos"][1]["box"] is True
    shutil.rmtree(tmpdir, ignore_errors=True)


def test_blocked_gate():
    b = boulder.new("t")
    boulder.add_todo(b, "1. fine")
    assert engine.should_run_wave(b, keep_going=False) is True
    assert engine.should_run_wave(b, keep_going=True) is True
    b2 = boulder.new("t")
    boulder.add_todo(b2, "1. broken [BLOCKED]")
    assert engine.should_run_wave(b2, keep_going=False) is False, "blocked+no-flag must skip wave"
    assert engine.should_run_wave(b2, keep_going=True) is True, "--keep-going must run wave anyway"


def test_save_load_preserves_boxes(tmpdir="/tmp/tony-test-p5c-rt"):
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)
    os.makedirs(tmpdir, exist_ok=True)
    b = boulder.new("rt")
    boulder.add_todo(b, "1. a", done=True)
    boulder.add_todo(b, "2. b")
    boulder.add_wave(b, "echo hi", done=True)
    p = os.path.join(tmpdir, "rt.md")
    open(p, "w").write(boulder.render(b))
    b2 = boulder.load(p)
    assert b2["todos"][0]["box"] is True and b2["todos"][1]["box"] is False
    assert b2["wave"][0]["box"] is True
    shutil.rmtree(tmpdir, ignore_errors=True)
