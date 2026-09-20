"""Critic v2 regression: strict VERDICT parse, rubric prompt, evidence coverage.

RED proof: importing critic_gate_detail / evidence_coverage / critic_prompt
before implementation must fail (ImportError or AttributeError).

GREEN: 8+ canned cases covering strict PASS/ISSUES, legacy fallback (weak),
BYPASS/PASSED traps, empty output, partial evidence, full evidence.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib import boulder
from lib import engine
from lib import score as score_mod
from lib import roles


# ---- helpers ----

def _b(*todo_texts):
    b = boulder.new("critic-v2-t")
    for t in todo_texts:
        boulder.add_todo(b, t)
    return b


# ---- critic_gate_detail tests ----

def test_strict_pass_strong():
    """Exact 'VERDICT: PASS' line -> strong=True, gate=PASS."""
    gate, strong = engine.critic_gate_detail("everything fine\nVERDICT: PASS\n")
    assert gate == "PASS"
    assert strong is True


def test_strict_issues_strong():
    """Exact 'VERDICT: ISSUES' line -> strong=True, gate=ISSUES."""
    gate, strong = engine.critic_gate_detail("VERDICT: ISSUES\nfound problems")
    assert gate == "ISSUES"
    assert strong is True


def test_legacy_pass_weak():
    """No strict VERDICT line but legacy 'PASS' word -> weak fallback, gate=PASS."""
    gate, strong = engine.critic_gate_detail("overall verdict: PASS\nall good")
    assert gate == "PASS"
    assert strong is False


def test_legacy_issues_weak():
    """No strict VERDICT, no PASS word -> weak fallback, gate=ISSUES."""
    gate, strong = engine.critic_gate_detail("some issues found\nno verdict line")
    assert gate == "ISSUES"
    assert strong is False


def test_bypass_trap_issues():
    """'BYPASS' must not match word-boundary PASS -> ISSUES."""
    gate, strong = engine.critic_gate_detail("VERDICT: BYPASS\nskip")
    assert gate == "ISSUES"


def test_passed_trap_issues():
    """'PASSED' must not match word-boundary PASS -> ISSUES."""
    gate, strong = engine.critic_gate_detail("VERDICT: PASSED\ndone")
    assert gate == "ISSUES"


def test_empty_issues():
    """Empty string -> ISSUES."""
    gate, strong = engine.critic_gate_detail("")
    assert gate == "ISSUES"


def test_none_issues():
    """None -> ISSUES."""
    gate, strong = engine.critic_gate_detail(None)
    assert gate == "ISSUES"


def test_legacy_gate_matches_critics_legacy():
    """critic_gate(str) returns same gate string as critic_gate_detail(str)[0] for all canned outputs."""
    cases = [
        "VERDICT: PASS",
        "VERDICT: ISSUES",
        "overall verdict: PASS",
        "some issues found",
        "VERDICT: BYPASS",
        "VERDICT: PASSED",
        "",
    ]
    for out in cases:
        d_gate, _ = engine.critic_gate_detail(out)
        l_gate = engine.critic_gate(out)
        assert d_gate == l_gate, f"mismatch for {out!r}"


# ---- evidence_coverage tests ----

def test_empty_todos_coverage():
    """Empty todo list -> 1.0 (nothing to cover)."""
    assert engine.evidence_coverage("any output", []) == 1.0


def test_no_evidence_coverage():
    """No TODO references in output -> 0.0."""
    assert engine.evidence_coverage("no references here", ["task a", "task b"]) == 0.0


def test_partial_evidence_coverage():
    """2 of 4 TODOs referenced -> 0.5."""
    out = "done TODO 1 and #3 are complete"
    assert engine.evidence_coverage(out, ["a", "b", "c", "d"]) == 0.5


def test_full_evidence_coverage():
    """All 3 TODOs referenced -> 1.0 (P19b: line-leading N. + TODO N + #N)."""
    out = "checked TODO 1\n#2\n3. done"
    assert engine.evidence_coverage(out, ["a", "b", "c"]) == 1.0


def test_todo_numbering_styles():
    """Mixed styles (TODO N, #N, line-leading N.) all count."""
    out = "TODO 1 done, #2 checked\n3. verified"
    assert engine.evidence_coverage(out, ["a", "b", "c", "d"]) == 0.75


def test_case_insensitive_todo():
    """'todo' in any case is recognized."""
    out = "Todo 1 and Todo 2 done"
    assert engine.evidence_coverage(out, ["a", "b", "c"]) == 2/3


# ---- score.compute with evidence param ----

def test_score_evidence_none_preserves_behavior():
    """evidence=None gives same result as old API (no evidence param)."""
    b = _b("task 1")
    b["wave"] = [{"box": True, "text": "F1. wave"}]
    r1 = score_mod.compute(b, "PASS")
    r2 = score_mod.compute(b, "PASS", evidence=None)
    assert r1 == r2, f"{r1} != {r2}"


def test_score_pass_full_evidence():
    """PASS + evidence=1.0 -> full critic_bonus (20)."""
    b = _b("task 1")
    b["wave"] = [{"box": True, "text": "F1. wave"}]
    b["todos"][0]["box"] = True
    r = score_mod.compute(b, "PASS", evidence=1.0)
    assert r["critic_bonus"] == 20, r
    assert r["score"] == 100, r


def test_score_pass_half_evidence():
    """PASS + evidence=0.5 -> critic_bonus scaled to 10."""
    b = _b("task 1")
    b["wave"] = [{"box": True, "text": "F1. wave"}]
    b["todos"][0]["box"] = True
    r = score_mod.compute(b, "PASS", evidence=0.5)
    assert r["critic_bonus"] == 10, r
    assert r["score"] == 90, r


def test_score_pass_zero_evidence():
    """PASS + evidence=0.0 -> critic_bonus=0."""
    b = _b("task 1")
    b["wave"] = [{"box": True, "text": "F1. wave"}]
    b["todos"][0]["box"] = True
    r = score_mod.compute(b, "PASS", evidence=0.0)
    assert r["critic_bonus"] == 0, r
    assert r["score"] == 80, r


def test_score_issues_evidence_irrelevant():
    """ISSUES + evidence=1.0 -> critic_bonus still 0."""
    b = _b("task 1")
    b["wave"] = [{"box": True, "text": "F1. wave"}]
    b["todos"][0]["box"] = True
    r = score_mod.compute(b, "ISSUES", evidence=1.0)
    assert r["critic_bonus"] == 0, r


# ---- roles.critic_prompt ----

def test_critics_system_constant():
    """CRITIC_SYSTEM string exists and is non-empty."""
    assert hasattr(roles, "CRITIC_SYSTEM")
    assert len(roles.CRITIC_SYSTEM) > 50


def test_critics_prompt_builder():
    """critic_prompt(boulder_md) returns str containing the boulder text."""
    md = "# Boulder: test\n## TODOs\n- [ ] 1. do stuff\n"
    result = roles.critic_prompt(md)
    assert isinstance(result, str)
    assert "test" in result
    assert md in result


# ---- runner (pytest broken: pluggy missing) ----

if __name__ == "__main__":
    tests = {k: v for k, v in sorted(globals().items()) if k.startswith("test_")}
    passed = failed = 0
    for name, fn in tests.items():
        try:
            fn()
            print(f"  PASS  {name}")
            passed += 1
        except (ImportError, AttributeError) as e:
            print(f"  RED   {name}: {type(e).__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  FAIL  {name}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed (RED = ImportError/AttributeError = expected before impl)")
    sys.exit(1 if failed else 0)
