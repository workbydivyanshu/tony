"""tests/test_critic_override.py — P22 RED: wave-after-failed-fix must be logged as an override.

Found live in P21: ISSUES -> builder fix FAILED -> wave still ran (--yes headless
contract), and the log chain never said so explicitly ("hold" -> "fix: fail" -> waves
PASS, no override line). God-level means the bypass is logged AS a bypass.

The P22 contract: apply_critic_gate returns (gate, fix_status); cmd_mission logs
"critic gate: ISSUES OVERRIDDEN — fix {status}, wave runs under --yes/headless;
treat wave results as UNVERIFIED-until-they-pass" before verify_wave when the fix
did not repair.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _boulder_two_todos():
    from lib import boulder as bmod
    b = bmod.new("override")
    bmod.add_todo(b, "1. one")
    bmod.add_todo(b, "2. two")
    return b


def test_apply_critic_gate_reports_fix_status():
    """ISSUES + fix_fn run -> (gate, fix status); PASS -> (gate, no fix)."""
    from lib import engine as eng
    b = _boulder_two_todos()
    gate, fix = eng.apply_critic_gate(b, "ISSUES", keep_going=False,
                                      fix_fn=lambda fails: None,
                                      critic_output="VERDICT: ISSUES")
    assert gate == "ISSUES"
    assert fix in ("ok", "fail", "held"), fix
    b = _boulder_two_todos()
    assert eng.apply_critic_gate(b, "PASS", keep_going=False)[0] == "PASS"


def test_failed_fix_marks_boulder_override():
    """ISSUES + FAILED fix -> boulder carries an explicit OVERRIDE line."""
    from lib import engine as eng
    b = _boulder_two_todos()
    eng.apply_critic_gate(b, "ISSUES", keep_going=False,
                          fix_fn=lambda fails: (_ for _ in ()).throw(RuntimeError("boom")),
                          critic_output="VERDICT: ISSUES")
    text = "\n".join(b["log"])
    assert "OVERRIDE" in text, text


def test_successful_fix_satisfies_gate():
    """ISSUES + successful fix -> fix documented ok (wave may proceed clean)."""
    from lib import engine as eng
    b = _boulder_two_todos()
    gate, fix = eng.apply_critic_gate(b, "ISSUES", keep_going=False,
                                      fix_fn=lambda fails: "ok",
                                      critic_output="VERDICT: ISSUES")
    assert fix == "ok", (gate, fix)


def test_mission_logs_override_before_wave():
    """cmd_mission must print the override wording when wave runs after a failed fix."""
    src = open(os.path.join(os.path.dirname(__file__), "..", "tony")).read()
    assert "OVERRIDE" in src, "mission path must speak the override contract"
