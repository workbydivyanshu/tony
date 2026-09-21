"""tests/test_submissions.py — submission pipeline contracts.

All tests name lib.submission and fail with ModuleNotFoundError because
the module does not yet exist. Each test documents one submission
invariant that lib.submission must satisfy when implemented.

Zero model burn, zero sleep, tmp HOME only (tempfile).
"""
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_tag_parse_mission_slug_and_missing():
    """[mission:slug] -> slug; missing/bad tag -> None."""
    import lib.submission as s
    home = tempfile.mkdtemp(prefix="tony-test-submissions-")
    try:
        assert s.tag_parse("[mission:build-v2]") == "build-v2"
        assert s.tag_parse("[mission:]") is None
        assert s.tag_parse("nope") is None
    finally:
        shutil.rmtree(home, ignore_errors=True)


def test_child_budget_600_to_300_and_90_floor():
    """child_budget(600) -> 300; child_budget(90) -> 60 floor."""
    import lib.submission as s
    assert s.child_budget(600) == 300
    assert s.child_budget(90) == 60


def test_depth_guard_depth2_tag_blocked():
    """depth-2 tag -> BLOCKED; mission_fn must not be called."""
    import lib.submission as s
    home = tempfile.mkdtemp(prefix="tony-test-submissions-")
    try:
        called = []
        res = s.execute(home, depth=2, mission_fn=lambda: called.append(True))
        assert res == "BLOCKED"
        assert called == []
    finally:
        shutil.rmtree(home, ignore_errors=True)


def test_max_children_fourth_tag_blocked():
    """4th child tag -> BLOCKED; max-children is 3."""
    import lib.submission as s
    home = tempfile.mkdtemp(prefix="tony-test-submissions-")
    try:
        tags = ["a", "b", "c", "d"]
        res = s.spawn_children(home, tags)
        assert res == "BLOCKED"
    finally:
        shutil.rmtree(home, ignore_errors=True)


def test_parent_flip_rules_72_green_59_red():
    """72+ green -> done; 59 -> BLOCKED; red-wave -> BLOCKED."""
    import lib.submission as s
    assert s.parent_flip(72, "green") == "done"
    assert s.parent_flip(59, "green") == "BLOCKED"
    assert s.parent_flip(72, "red") == "BLOCKED"


def test_summary_bounds_three_lines_160_chars():
    """summary must be <=3 lines and <=160 chars."""
    import lib.submission as s
    home = tempfile.mkdtemp(prefix="tony-test-submissions-")
    try:
        summary = s.summarize(home, "ok")
        lines = summary.splitlines()
        assert len(lines) <= 3, summary
        assert len(summary) <= 160, summary
    finally:
        shutil.rmtree(home, ignore_errors=True)


def test_hostile_child_wave_blocked_unexecuted():
    """Hostile child wave -> BLOCKED; wave commands never executed."""
    import lib.submission as s
    home = tempfile.mkdtemp(prefix="tony-test-submissions-")
    try:
        executed = []
        res = s.run_wave(home, "rm -rf /", executed.append)
        assert res == "BLOCKED"
        assert executed == []
    finally:
        shutil.rmtree(home, ignore_errors=True)


def test_architect_prompt_tag_docs():
    """Architect prompt must include tag documentation."""
    import lib.submission as s
    prompt = s.architect_prompt()
    assert "[mission:" in prompt
    assert "BLOCKED" in prompt
    assert "child_budget" in prompt


def test_engine_mission_tag_depth_blocked():
    """run_loop depth=2 + [mission:] tag -> BLOCKED, mission_fn uncalled."""
    from lib import engine, boulder
    import shutil
    tmpdir = tempfile.mkdtemp(prefix="tony-test-submissions-eng-")
    try:
        b = boulder.new("t-sub-depth")
        boulder.add_todo(b, "[mission:probe] survey auth call sites")
        called = []
        engine.run_loop(b, {"builder": []}, workdir=tmpdir,
                        runner=lambda *a, **k: (_ for _ in ()).throw(
                            AssertionError("model runner must not run")),
                        runslog=os.path.join(tmpdir, "runs.log"),
                        depth=2, mission_fn=lambda *a, **k: called.append(True))
        assert called == [], called
        assert "BLOCKED" in b["todos"][0]["text"], b["todos"]
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_engine_mission_tag_happy_flips():
    """run_loop depth=0 + mission_fn score 72 green -> TODO done."""
    from lib import engine, boulder
    import shutil
    tmpdir = tempfile.mkdtemp(prefix="tony-test-submissions-eng-")
    try:
        b = boulder.new("t-sub-happy")
        boulder.add_todo(b, "[mission:recon-auth] survey auth call sites")
        engine.run_loop(
            b, {"builder": []}, workdir=tmpdir,
            runner=lambda *a, **k: (_ for _ in ()).throw(
                AssertionError("model runner must not run")),
            runslog=os.path.join(tmpdir, "runs.log"),
            depth=0, mission_fn=lambda *a, **k: {"score": 72,
                                                 "wave_green": True,
                                                 "summary": "surveyed 3 sites"})
        assert b["todos"][0]["box"] is True, b["todos"]
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_engine_mission_tag_score_floor_blocked():
    """run_loop mission_fn score 59 green -> TODO BLOCKED (floor 60)."""
    from lib import engine, boulder
    import shutil
    tmpdir = tempfile.mkdtemp(prefix="tony-test-submissions-eng-")
    try:
        b = boulder.new("t-sub-floor")
        boulder.add_todo(b, "[mission:thin] weak survey")
        engine.run_loop(
            b, {"builder": []}, workdir=tmpdir,
            runner=lambda *a, **k: (_ for _ in ()).throw(
                AssertionError("model runner must not run")),
            runslog=os.path.join(tmpdir, "runs.log"),
            depth=0, mission_fn=lambda *a, **k: {"score": 59,
                                                 "wave_green": True,
                                                 "summary": "thin"})
        assert b["todos"][0]["box"] is not True, b["todos"]
        assert "BLOCKED" in b["todos"][0]["text"], b["todos"]
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_roles_architect_documents_mission_tag():
    """Real architect prompt must document the [mission:] tag."""
    from lib import roles
    prompt = roles.architect_prompt("probe mission")
    assert "[mission:" in prompt, prompt[:400]
