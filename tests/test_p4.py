"""P4 RED proof: wave execution + sanitize + report must exist."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib import engine, boulder, report

def test_wave_executes():
    b = boulder.new("t")
    boulder.add_wave(b, "echo hello")
    boulder.add_wave(b, "false")
    res = engine.run_wave(b, cwd="/tmp")
    assert res == [True, False], res
    assert b["wave"][0]["box"] is True and b["wave"][1]["box"] is False

def test_wave_strips_f_labels():
    # e2e F2 bug: boulder wave items carry "F1. " labels; the shell must get the bare command.
    b = boulder.new("t")
    boulder.add_wave(b, "F1. echo label-test-ok")
    res = engine.run_wave(b, cwd="/tmp")
    assert res == [True], res
    assert b["wave"][0]["box"] is True

def test_sanitize():
    raw = "\x1b[0m> Sisyphus stuff\x1b[0m\n# Boulder: x\n## TODOs\n- [ ] 1. thing\n## Final Verification Wave\n- [ ] F1. echo hi\n## Progress Log\n"
    b = boulder.parse(engine.sanitize(raw))
    assert b["title"] == "x" and len(b["todos"]) == 1
    assert "\x1b" not in engine.sanitize(raw)

def test_report(tmpdir="/tmp/tony-test-report"):
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)
    b = boulder.new("demo")
    boulder.add_todo(b, "1. did it"); b["todos"][0]["box"] = True
    boulder.add_wave(b, "echo hi"); b["wave"][0]["box"] = True
    p = report.write(tmpdir, "demo", "do stuff", {"builder": "m"}, b, 95, "clean")
    txt = open(p).read()
    assert "MISSION SCORE: 95/100" in txt and "do stuff" in txt, txt
