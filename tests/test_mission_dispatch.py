"""P38 mission-dispatch pins (engine wave): mission_fn=None hold, resume re-fire/skip.

Split from test_mission_evidence.py — these need the engine dispatch hook
(_exec_one mission branch), not doctrine. RED until that wave lands.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── 4. mission_fn=None honest hold (engine dispatch wave) ────────────

def test_mission_fn_none_blocked():
    """run_loop with mission_fn=None holds the mission TODO as BLOCKED."""
    from lib import boulder, engine
    b = boulder.new("t-none-hold")
    boulder.add_todo(b, "[mission:ghost] do the thing")
    engine.run_loop(b, {"builder": ["m1"]}, workdir="/tmp",
                    mission_fn=None)
    assert "[BLOCKED" in b["todos"][0]["text"], b["todos"]


# ── 5. resume re-dispatch (engine dispatch wave) ─────────────────────

def test_resume_redispatch_unchecked_mission():
    """A failing mission stays visible and re-fires (no silent loss)."""
    from lib import boulder, engine
    calls = []
    b = boulder.new("t-resume-redispatch")
    boulder.add_todo(b, "[mission:again] do it twice")
    def fn(text, slug):
        calls.append((text, slug))
        return (30, False)
    engine.run_loop(b, {"builder": ["m1"]}, workdir="/tmp", mission_fn=fn)
    assert b["todos"][0]["box"] is False, b["todos"]
    assert "[BLOCKED" in b["todos"][0]["text"], b["todos"]
    engine.run_loop(b, {"builder": ["m1"]}, workdir="/tmp", mission_fn=fn)
    assert len(calls) == 2, calls


def test_resume_skips_completed_mission():
    """A completed (flipped) mission TODO never re-fires."""
    from lib import boulder, engine
    calls = []
    b = boulder.new("t-resume-skip")
    boulder.add_todo(b, "[mission:once] do it once")
    def fn(text, slug):
        calls.append((text, slug))
        return (80, True)
    engine.run_loop(b, {"builder": ["m1"]}, workdir="/tmp", mission_fn=fn)
    assert b["todos"][0]["box"] is True, b["todos"]
    engine.run_loop(b, {"builder": ["m1"]}, workdir="/tmp", mission_fn=fn)
    assert len(calls) == 1, calls


