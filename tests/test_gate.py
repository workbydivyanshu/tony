"""Gate-path regression pins: the live-F2 UnboundLocalError class must stay dead.

apply_critic_gate takes fix_fn as a parameter, so call-before-def ordering
crashes are structurally impossible. These pins lock the behavior.
"""
import sys, os, shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib import engine, boulder


def _b():
    b = boulder.new("gate-t")
    boulder.add_todo(b, "1. a")
    return b


def test_gate_pass_no_fix():
    b = _b()
    calls = []
    g = engine.apply_critic_gate(b, "PASS", fix_fn=lambda f: calls.append(f))
    assert g == "PASS"
    assert calls == []
    assert any("critic gate: PASS" in l for l in b["log"])


def test_gate_issues_fix_once_hold():
    b = _b()
    calls = []
    g = engine.apply_critic_gate(b, "ISSUES", fix_fn=lambda f: calls.append(f),
                                 critic_output="ISSUES: x")
    assert g == "ISSUES"
    assert calls == [["ISSUES: x"]]
    assert any("holding wave for builder fix" in l for l in b["log"])


def test_gate_issues_keep_going_override_no_fix():
    b = _b()
    calls = []
    g = engine.apply_critic_gate(b, "ISSUES", keep_going=True,
                                 fix_fn=lambda f: calls.append(f),
                                 critic_output="ISSUES: x")
    assert g == "ISSUES"
    assert calls == []
    assert any("overridden by --keep-going" in l for l in b["log"])


def test_gate_issues_no_fix_fn_honest_hold():
    b = _b()
    g = engine.apply_critic_gate(b, "ISSUES", fix_fn=None, critic_output="ISSUES: x")
    assert g == "ISSUES"
    assert any("holding wave for builder fix" in l for l in b["log"])
