"""tests/test_p39_oracle_gates.py — oracle review gate pins for P38 follow-up.

Four issues flagged by oracle review (ses_f3afa3a68ffeyj9nBBlP23vfea):
1. Combo-tag dispatch: [role:X] [mission:slug] bypasses mission guard
2. Waveguard routing: child waves must use waveguard.check, not submission._is_hostile
3. Malformed-tag fallthrough: tag_parse None must clamp to BLOCKED, not role_call
4. Doctrine wording: roles.py says "depth > 2" but code blocks at depth >= 2

Zero model burn, zero sleep, tmp HOME only (tempfile).
"""
import os
import re
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# --- Gate 1: combo-tag dispatch ---

def test_combo_tag_role_mission_dispatches_as_mission():
    """[role:builder] [mission:probe] must dispatch via mission_fn, not role_call.

    Oracle note 1: _MISSION_TAG_RE.match() only matches at string start.
    A [role:X] prefix causes silent bypass to role_call."""
    from lib import engine, boulder
    tmpdir = tempfile.mkdtemp(prefix="tony-test-p39-")
    try:
        b = boulder.new("t-combo-tag")
        boulder.add_todo(b, "[role:builder] [mission:probe] survey auth")
        called = []
        engine.run_loop(
            b, {"builder": []}, workdir=tmpdir,
            runner=lambda *a, **k: (_ for _ in ()).throw(
                AssertionError("role_call runner must NOT run for mission tags")),
            runslog=os.path.join(tmpdir, "runs.log"),
            depth=0, mission_fn=lambda *a, **k: (
                called.append(True) or {"score": 80, "wave_green": True,
                                        "summary": "probed"}))
        assert called, "mission_fn was never called — combo tag bypassed to role_call"
        assert b["todos"][0]["box"] is True, b["todos"]
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_combo_tag_depth2_blocked():
    """[role:explorer] [mission:deep] at depth=2 must BLOCKED, not role_call."""
    from lib import engine, boulder
    tmpdir = tempfile.mkdtemp(prefix="tony-test-p39-")
    try:
        b = boulder.new("t-combo-depth")
        boulder.add_todo(b, "[role:explorer] [mission:deep] go deep")
        engine.run_loop(
            b, {"explorer": []}, workdir=tmpdir,
            runner=lambda *a, **k: (_ for _ in ()).throw(
                AssertionError("runner must NOT run")),
            runslog=os.path.join(tmpdir, "runs.log"),
            depth=2, mission_fn=lambda *a, **k: (_ for _ in ()).throw(
                AssertionError("mission_fn must NOT run at depth 2")))
        assert "BLOCKED" in b["todos"][0]["text"], b["todos"]
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# --- Gate 2: waveguard routing (no submission._is_hostile drift) ---

def test_submission_run_wave_uses_waveguard():
    """submission.run_wave must delegate to waveguard.check, not its own _is_hostile.

    Oracle note 2: submission.py has a duplicated _is_hostile deny-list that
    will drift from waveguard.py. Real child waves must route through waveguard."""
    import lib.submission as sub
    # A command that waveguard blocks but submission._is_hostile might miss
    # (device node write — in waveguard._DENY but NOT in submission._is_hostile):
    executed = []
    res = sub.run_wave("/tmp/t", "echo x > /dev/sda1", executed.append)
    assert res == "BLOCKED", f"waveguard should block device write, got {res}"
    assert executed == [], "hostile command was executed"


def test_submission_no_private_is_hostile():
    """submission.py must NOT define _is_hostile (waveguard is the single authority).

    Oracle note 2: drift risk — two deny-lists = guaranteed divergence."""
    import lib.submission as sub
    assert not hasattr(sub, "_is_hostile"), \
        "submission.py still has _is_hostile — must route through waveguard.check"


# --- Gate 3: malformed-tag fallthrough ---

def test_malformed_mission_tag_clamps_blocked():
    """[mission:] (empty slug) must BLOCKED, not fall through to role_call.

    Oracle note 3: tag_parse returns None for malformed tags, but the current
    code only checks the match, not the parse result — malformed tags fall
    through to resolve_role."""
    from lib import engine, boulder
    tmpdir = tempfile.mkdtemp(prefix="tony-test-p39-")
    try:
        b = boulder.new("t-malformed")
        boulder.add_todo(b, "[mission:] empty slug survey")
        engine.run_loop(
            b, {"builder": []}, workdir=tmpdir,
            runner=lambda *a, **k: (_ for _ in ()).throw(
                AssertionError("runner must NOT run for malformed mission tag")),
            runslog=os.path.join(tmpdir, "runs.log"),
            depth=0, mission_fn=lambda *a, **k: (_ for _ in ()).throw(
                AssertionError("mission_fn must NOT run for malformed tag")))
        assert "BLOCKED" in b["todos"][0]["text"], \
            f"malformed tag fell through: {b['todos']}"
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_whitespace_only_slug_clamps_blocked():
    """[mission:   ] (whitespace slug) must BLOCKED, not fall through."""
    from lib import engine, boulder
    tmpdir = tempfile.mkdtemp(prefix="tony-test-p39-")
    try:
        b = boulder.new("t-ws-slug")
        boulder.add_todo(b, "[mission:   ] whitespace slug")
        engine.run_loop(
            b, {"builder": []}, workdir=tmpdir,
            runner=lambda *a, **k: (_ for _ in ()).throw(
                AssertionError("runner must NOT run")),
            runslog=os.path.join(tmpdir, "runs.log"),
            depth=0, mission_fn=lambda *a, **k: (_ for _ in ()).throw(
                AssertionError("mission_fn must NOT run")))
        assert "BLOCKED" in b["todos"][0]["text"], \
            f"whitespace slug fell through: {b['todos']}"
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# --- Gate 4: doctrine wording off-by-one ---

def test_doctrine_depth_wording_gte_not_gt():
    """Architect doctrine must say depth >= 2 (or 'at depth 2'), not 'depth > 2'.

    Oracle note 4: code blocks at depth>=2 but doctrine says '> 2', which
    suggests depth 2 is allowed. The code is correct; the wording is wrong."""
    from lib import roles
    prompt = roles.architect_prompt("probe mission")
    # Must NOT contain "depth > 2" (off-by-one wording)
    assert "depth > 2" not in prompt, \
        f"doctrine says 'depth > 2' but code blocks at depth >= 2: {prompt[:300]}"
    # Must contain correct wording (depth >= 2 or equivalent)
    assert re.search(r"depth\s*(?:>=|≥)\s*2|at depth 2", prompt), \
        f"doctrine missing correct depth guard wording: {prompt[:300]}"


# --- Cross-check: existing behavior still holds ---

def test_pure_mission_tag_still_dispatches():
    """[mission:slug] (no role prefix) still works — regression guard."""
    from lib import engine, boulder
    tmpdir = tempfile.mkdtemp(prefix="tony-test-p39-")
    try:
        b = boulder.new("t-pure-tag")
        boulder.add_todo(b, "[mission:clean-auth] clean up auth module")
        called = []
        engine.run_loop(
            b, {"builder": []}, workdir=tmpdir,
            runner=lambda *a, **k: (_ for _ in ()).throw(
                AssertionError("runner must NOT run")),
            runslog=os.path.join(tmpdir, "runs.log"),
            depth=0, mission_fn=lambda *a, **k: (
                called.append(True) or {"score": 75, "wave_green": True,
                                        "summary": "cleaned"}))
        assert called, "mission_fn was not called for pure tag"
        assert b["todos"][0]["box"] is True, b["todos"]
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_children_count_with_combo_tags():
    """Mission-tag children counter must count combo tags too."""
    from lib import engine, boulder
    tmpdir = tempfile.mkdtemp(prefix="tony-test-p39-")
    try:
        b = boulder.new("t-combo-children")
        # 4 mission tags — mix of pure and combo — 4th must BLOCKED
        boulder.add_todo(b, "[mission:a] first")
        boulder.add_todo(b, "[role:builder] [mission:b] second")
        boulder.add_todo(b, "[mission:c] third")
        boulder.add_todo(b, "[role:explorer] [mission:d] fourth should block")
        called = [0]

        def counting_fn(*a, **k):
            called[0] += 1
            return {"score": 80, "wave_green": True, "summary": "ok"}

        engine.run_loop(
            b, {"builder": [], "explorer": []}, workdir=tmpdir,
            runner=lambda *a, **k: (_ for _ in ()).throw(
                AssertionError("runner must NOT run")),
            runslog=os.path.join(tmpdir, "runs.log"),
            depth=0, mission_fn=counting_fn, max_children=3)
        assert called[0] == 3, f"expected 3 calls, got {called[0]}"
        assert "BLOCKED" in b["todos"][3]["text"], \
            f"4th tag should be BLOCKED: {b['todos'][3]}"
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
