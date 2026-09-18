"""P1 RED proof: lib.score must not exist yet; compute() is the wave-gated scorer.

Importing lib.score before implementation raises ImportError.
Once lib/score.py exists, all cases below must pass.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib import boulder


def _make_b(todo_done=0, todo_total=1, wave_done=0, wave_total=1, blocked=False):
    b = boulder.new("score-t")
    for i in range(todo_total):
        boulder.add_todo(b, f"{i+1}. task", done=(i < todo_done))
    for i in range(wave_total):
        boulder.add_wave(b, f"F{i+1}. wave", done=(i < wave_done))
    if blocked:
        b["todos"][0]["text"] = "[BLOCKED] something"
    return b


def _run_score():
    """Import and call compute. Fails with ImportError before lib/score.py exists."""
    from lib.score import compute
    return compute


# --- GREEN cases ---
def test_perfect_100():
    compute = _run_score()
    b = _make_b(todo_done=1, todo_total=1, wave_done=1, wave_total=1)
    r = compute(b, "PASS")
    assert r["score"] == 100, r
    assert r["todo_frac"] == 1.0
    assert r["wave_frac"] == 1.0
    assert r["critic_bonus"] == 20
    assert r["capped"] is False


def test_empty_wave_caps_at_40():
    compute = _run_score()
    b = _make_b(todo_done=1, todo_total=1, wave_done=0, wave_total=0)
    r = compute(b, "PASS")
    assert r["score"] == 40, r
    assert r["capped"] is True


def test_blocked_caps_at_49():
    compute = _run_score()
    b = _make_b(todo_done=1, todo_total=1, wave_done=1, wave_total=1, blocked=True)
    r = compute(b, "PASS")
    assert r["score"] == 49, r
    assert r["capped"] is True


def test_issues_zeroes_bonus():
    compute = _run_score()
    b = _make_b(todo_done=1, todo_total=1, wave_done=1, wave_total=1)
    r = compute(b, "ISSUES")
    assert r["score"] == 80, r
    assert r["critic_bonus"] == 0
    assert r["capped"] is False


def test_na_half_bonus():
    compute = _run_score()
    b = _make_b(todo_done=1, todo_total=1, wave_done=1, wave_total=1)
    r = compute(b, "N/A")
    assert r["score"] == 90, r
    assert r["critic_bonus"] == 10
    assert r["capped"] is False


def test_total_fail_0():
    compute = _run_score()
    b = _make_b(todo_done=0, todo_total=1, wave_done=0, wave_total=1)
    r = compute(b, "ISSUES")
    assert r["score"] == 0, r
    assert r["capped"] is False
