"""V1 Task 5 RED proof: CLI wiring — score helper, --tui, --timeout.

Tests MUST fail against current tony (no cmd_score, no --tui, no --timeout
plumbing through run_loop). All tests use fake runners — zero live burn.
Plain-assert style (pytest broken in this env).
"""
import sys
import os
import types
import inspect
import importlib.util
import importlib.machinery

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib import boulder, score as score_mod


def _load_tony():
    """Load tony script as a module (no .py extension)."""
    path = os.path.join(os.path.dirname(__file__), "..", "tony")
    loader = importlib.machinery.SourceFileLoader("tony", path)
    spec = importlib.util.spec_from_file_location("tony", path, loader=loader)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── Helpers ──────────────────────────────────────────────────────────────

def _b(**kw):
    """Build a quick boulder with given todo/wave state."""
    b = boulder.new("cli-wire-t")
    todo_done = kw.get("todo_done", 0)
    todo_total = kw.get("todo_total", 1)
    wave_done = kw.get("wave_done", 0)
    wave_total = kw.get("wave_total", 1)
    blocked = kw.get("blocked", False)
    for i in range(todo_total):
        boulder.add_todo(b, f"{i+1}. task", done=(i < todo_done))
    for i in range(wave_total):
        boulder.add_wave(b, f"F{i+1}. wave", done=(i < wave_done))
    if blocked:
        b["todos"][0]["text"] = "[BLOCKED] something"
    return b


# ── cmd_score helper tests ───────────────────────────────────────────────

def test_cmd_score_exists():
    """cmd_score must be importable from tony."""
    tony = _load_tony()
    assert hasattr(tony, "cmd_score"), "tony must export cmd_score"


def test_cmd_score_returns_int():
    """cmd_score(b, gate, evidence) returns an int (score value)."""
    tony = _load_tony()
    b = _b(todo_done=1, todo_total=1, wave_done=1, wave_total=1)
    result = tony.cmd_score(b, "PASS", None)
    assert isinstance(result, int), f"expected int, got {type(result)}"


def test_cmd_score_perfect_100():
    """All done + PASS -> 100."""
    tony = _load_tony()
    b = _b(todo_done=1, todo_total=1, wave_done=1, wave_total=1)
    assert tony.cmd_score(b, "PASS", None) == 100


def test_cmd_score_blocked_caps_49():
    """BLOCKED TODO -> score capped at 49."""
    tony = _load_tony()
    b = _b(todo_done=1, todo_total=1, wave_done=1, wave_total=1, blocked=True)
    assert tony.cmd_score(b, "PASS", None) == 49


def test_cmd_score_issues_no_bonus():
    """ISSUES gate zeroes bonus -> 80."""
    tony = _load_tony()
    b = _b(todo_done=1, todo_total=1, wave_done=1, wave_total=1)
    assert tony.cmd_score(b, "ISSUES", None) == 80


def test_cmd_score_na_zero_bonus():
    """P19c: N/A gate -> zero bonus -> 80 (no critic, no free points)."""
    tony = _load_tony()
    b = _b(todo_done=1, todo_total=1, wave_done=1, wave_total=1)
    assert tony.cmd_score(b, "N/A", None) == 80


def test_cmd_score_empty_wave_caps_40():
    """Empty wave list -> cap at 40."""
    tony = _load_tony()
    b = _b(todo_done=1, todo_total=1, wave_done=0, wave_total=0)
    assert tony.cmd_score(b, "PASS", None) == 40


def test_cmd_score_total_fail_0():
    """Nothing done + ISSUES -> 0."""
    tony = _load_tony()
    b = _b(todo_done=0, todo_total=1, wave_done=0, wave_total=1)
    assert tony.cmd_score(b, "ISSUES", None) == 0


def test_cmd_score_with_evidence():
    """PASS + evidence=0.5 -> critic_bonus scaled by coverage."""
    tony = _load_tony()
    b = _b(todo_done=1, todo_total=1, wave_done=1, wave_total=1)
    # Full evidence = 1.0 -> 100.  evidence 0.5 -> 40+40+10 = 90
    score = tony.cmd_score(b, "PASS", 0.5)
    assert score == 90, f"expected 90, got {score}"


def test_cmd_score_delegates_to_score_compute():
    """cmd_score must call score.compute, not inline math."""
    tony = _load_tony()
    b = _b(todo_done=1, todo_total=1, wave_done=1, wave_total=1)
    r = score_mod.compute(b, "PASS", None)
    assert tony.cmd_score(b, "PASS", None) == r["score"]


# ── --timeout plumbing tests ─────────────────────────────────────────────

def test_run_loop_accepts_timeout():
    """engine.run_loop signature must include timeout parameter."""
    import inspect
    from lib import engine
    sig = inspect.signature(engine.run_loop)
    assert "timeout" in sig.parameters, f"run_loop missing timeout param: {list(sig.parameters)}"


def test_exec_one_accepts_timeout():
    """engine._exec_one signature must include timeout parameter."""
    import inspect
    from lib import engine
    sig = inspect.signature(engine._exec_one)
    assert "timeout" in sig.parameters, f"_exec_one missing timeout param: {list(sig.parameters)}"


def test_timeout_default_600():
    """Both run_loop and _exec_one default timeout to 600."""
    import inspect
    from lib import engine
    rl_def = inspect.signature(engine.run_loop).parameters["timeout"].default
    eo_def = inspect.signature(engine._exec_one).parameters["timeout"].default
    assert rl_def == 600, f"run_loop timeout default: {rl_def}"
    assert eo_def == 600, f"_exec_one timeout default: {eo_def}"


def test_timeout_captured_by_fake_runner():
    """timeout=42 passed through run_loop -> role_call -> runner kwarg,
    scaled by the role budget (P17: builder gets 0.8 * 42 = 33)."""
    import shutil
    from lib import engine, boulder as bmod

    TMP = "/tmp/tony-test-timeout-wire"
    shutil.rmtree(TMP, ignore_errors=True)
    os.makedirs(TMP, exist_ok=True)

    captured = []

    def fake_runner(cmd, **kw):
        captured.append(kw)
        class R: returncode = 0; stdout = "OK"; stderr = ""
        return R()

    b = bmod.new("t")
    bmod.add_todo(b, "1. thing")
    engine.run_loop(b, {"builder": ["m1"]}, workdir=TMP,
                    runner=fake_runner,
                    runslog=os.path.join(TMP, "runs.log"),
                    timeout=42)
    assert len(captured) >= 1, "runner should have been called"
    assert captured[0].get("timeout") == 33, f"expected builder budget 0.8*42=33, got {captured[0]}"


def test_timeout_600_captured_when_default():
    """Default timeout=600 flows through to runner, scaled by role budget
    (P17: builder 0.8 * 600 = 480)."""
    import shutil
    from lib import engine, boulder as bmod

    TMP = "/tmp/tony-test-timeout-default"
    shutil.rmtree(TMP, ignore_errors=True)
    os.makedirs(TMP, exist_ok=True)

    captured = []

    def fake_runner(cmd, **kw):
        captured.append(kw)
        class R: returncode = 0; stdout = "OK"; stderr = ""
        return R()

    b = bmod.new("t")
    bmod.add_todo(b, "1. thing")
    engine.run_loop(b, {"builder": ["m1"]}, workdir=TMP,
                    runner=fake_runner,
                    runslog=os.path.join(TMP, "runs.log"))
    assert len(captured) >= 1
    assert captured[0].get("timeout") == 480, f"expected builder budget 0.8*600=480, got {captured[0]}"


# ── --tui flag tests ─────────────────────────────────────────────────────

def test_tui_flag_in_help():
    """--tui must appear in --help output."""
    import subprocess
    result = subprocess.run([sys.executable, "tony", "--help"],
                            capture_output=True, text=True,
                            cwd=os.path.join(os.path.dirname(__file__), ".."))
    assert "--tui" in result.stdout, f"--tui missing from --help:\n{result.stdout[:500]}"


def test_timeout_flag_in_help():
    """--timeout must appear in --help output."""
    import subprocess
    result = subprocess.run([sys.executable, "tony", "--help"],
                            capture_output=True, text=True,
                            cwd=os.path.join(os.path.dirname(__file__), ".."))
    assert "--timeout" in result.stdout, f"--timeout missing from --help:\n{result.stdout[:500]}"


def test_tui_fallback_no_tty():
    """--tui with no TTY prints fallback notice and returns 1."""
    from lib import tui

    tony = _load_tony()

    # Mock should_use_curses to return False
    orig = tui.should_use_curses
    tui.should_use_curses = lambda: False
    try:
        # --tui on nonexistent slug with no TTY -> fallback notice -> poll -> exit 2 (no boulder)
        rc = tony.main(["--tui", "__nosuch__slug__"])
        assert rc == 2, f"expected exit 2 for missing boulder, got {rc}"
    finally:
        tui.should_use_curses = orig


def test_tui_calls_run_tui_when_tty():
    """--tui with TTY delegates to run_tui (fake it)."""
    from lib import tui
    tony = _load_tony()

    # Prepare a real boulder for run_tui to load
    slug = "tui-wire-test"
    b = boulder.new(slug)
    boulder.add_todo(b, "1. test item")
    bpath = boulder.save(slug, b)

    run_tui_calls = []
    orig_should = tui.should_use_curses
    orig_run = tui.run_tui

    tui.should_use_curses = lambda: True
    tui.run_tui = lambda s, **kw: run_tui_calls.append(s) or 0
    try:
        rc = tony.main(["--tui", slug])
        assert rc == 0, f"expected 0, got {rc}"
        assert run_tui_calls == [slug], f"run_tui not called with slug: {run_tui_calls}"
    finally:
        tui.should_use_curses = orig_should
        tui.run_tui = orig_run
        os.unlink(bpath)


# ── Inline 100*(done... must be gone ────────────────────────────────────

def test_no_inline_score_in_tony():
    """grep '100 * (done' tony must be empty — inline computations deleted from CLI."""
    tony_path = os.path.join(os.path.dirname(__file__), "..", "tony")
    with open(tony_path) as f:
        content = f.read()
    assert "100 * (done" not in content, \
        "inline '100 * (done...' computation still present in tony"


# ── Existing flags still work (read-only smoke) ─────────────────────────

def test_version_flag():
    """--version still works."""
    import subprocess
    result = subprocess.run([sys.executable, "tony", "--version"],
                            capture_output=True, text=True,
                            cwd=os.path.join(os.path.dirname(__file__), ".."))
    assert result.returncode == 0
    assert "tony" in result.stdout.lower()


def test_watch_nonexistent_exit2():
    """--watch __nosuch__ --once exits 2."""
    import subprocess
    result = subprocess.run(
        [sys.executable, "tony", "--watch", "__nosuch__watch__", "--once"],
        capture_output=True, text=True,
        cwd=os.path.join(os.path.dirname(__file__), ".."))
    assert result.returncode == 2, f"expected exit 2, got {result.returncode}"
