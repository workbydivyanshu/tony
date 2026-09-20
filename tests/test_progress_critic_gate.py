"""P5c-2 RED proof: progress + render_snapshot + critic_gate."""
import sys
import os
import shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib import engine, boulder, watch


# --- RED: new symbols do not exist yet (proven by the call-sites below
# raising AttributeError/NameError; no negative assertions — they would
# invert when the symbols land) ---


# --- boulder.progress semantics (RED: AttributeError on call) ---

def test_progress_returns_dict_shape():
    b = boulder.new("t")
    boulder.add_todo(b, "1. a")
    boulder.add_wave(b, "echo hi")
    r = boulder.progress(b)  # AttributeError: progress not defined
    assert set(r.keys()) == {"done", "total", "waved", "wavetotal", "score", "blocked"}


def test_progress_score_formula():
    b = boulder.new("t")
    boulder.add_todo(b, "1. a", done=True)
    boulder.add_wave(b, "echo hi", done=True)
    r = boulder.progress(b)  # AttributeError: progress not defined
    assert r["score"] == 100 * (1 + 1) / max(1, 1 + 1)


def test_progress_empty_boulder():
    b = boulder.new("t")
    r = boulder.progress(b)  # AttributeError: progress not defined
    assert r["score"] == 0


# --- watch.render_snapshot semantics (RED: NameError/AttributeError) ---

def test_render_snapshot_contains_pane_headers():
    b = boulder.new("t")
    boulder.add_todo(b, "1. a")
    boulder.add_wave(b, "echo hi")
    s = watch.render_snapshot(b, [], [], {})  # NameError: watch not imported
    assert "TODOs" in s and "wave" in s


def test_render_snapshot_empty_boulder_safe():
    b = boulder.new("t")
    s = watch.render_snapshot(b, [], [], {})  # NameError: watch not imported
    assert isinstance(s, str) and len(s) > 0


def test_render_snapshot_truncates_long_lines():
    b = boulder.new("t")
    boulder.add_todo(b, "x" * 500)
    s = watch.render_snapshot(b, [], [], {})  # NameError: watch not imported
    for line in s.splitlines():
        assert len(line) <= 200, f"line too long: {len(line)}"


# --- engine.critic_gate semantics (RED: AttributeError on call) ---

def test_critic_gate_pass_on_pass():
    assert engine.critic_gate("PASS") == "PASS"  # AttributeError: critic_gate not defined


def test_critic_gate_pass_case_insensitive():
    assert engine.critic_gate("pass") == "PASS"  # AttributeError: critic_gate not defined


def test_critic_gate_issues_on_fail():
    assert engine.critic_gate("something wrong") == "ISSUES"  # AttributeError


def test_critic_gate_none_is_issues():
    assert engine.critic_gate(None) == "ISSUES"  # AttributeError


def test_critic_gate_empty_is_issues():
    assert engine.critic_gate("") == "ISSUES"  # AttributeError


def test_critic_gate_bypass_not_match():
    assert engine.critic_gate("BYPASS") == "ISSUES"  # AttributeError: word-boundary PASS only


def test_critic_gate_word_boundary_not_substring():
    assert engine.critic_gate("PASSED") == "ISSUES"  # AttributeError: PASS is substring, not word-boundary


# --- fake-runner gate test shape: echo/false wave items, per-test tmpdirs ---

def test_fake_runner_pass_wave_runs():
    tmpdir = "/tmp/tony-test-p5c2-fake-pass"
    shutil.rmtree(tmpdir, ignore_errors=True)
    os.makedirs(tmpdir, exist_ok=True)
    b = boulder.new("t")
    boulder.add_wave(b, "echo ok")
    res = engine.run_wave(b, cwd=tmpdir)
    assert res == [True], res
    shutil.rmtree(tmpdir, ignore_errors=True)


def test_fake_runner_issues_fix_once():
    tmpdir = "/tmp/tony-test-p5c2-fake-issues"
    shutil.rmtree(tmpdir, ignore_errors=True)
    os.makedirs(tmpdir, exist_ok=True)
    b = boulder.new("t")
    boulder.add_wave(b, "false")
    fix_calls = [0]

    def fix_fn(fails):
        fix_calls[0] += 1

    res = engine.verify_wave(b, max_verify=2, cwd=tmpdir, fix_fn=fix_fn)
    assert res == [False], res
    assert fix_calls[0] == 1, f"fix must run once between attempts, got {fix_calls[0]}"
    assert any("exhausted (2 attempts)" in l for l in b["log"]), b["log"]
    shutil.rmtree(tmpdir, ignore_errors=True)


def test_fake_runner_mixed_echo_false():
    tmpdir = "/tmp/tony-test-p5c2-fake-mixed"
    shutil.rmtree(tmpdir, ignore_errors=True)
    os.makedirs(tmpdir, exist_ok=True)
    b = boulder.new("t")
    boulder.add_wave(b, "echo ok")
    boulder.add_wave(b, "false")
    res = engine.run_wave(b, cwd=tmpdir)
    assert res == [True, False], res
    shutil.rmtree(tmpdir, ignore_errors=True)
