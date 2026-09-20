"""tests/test_selftest.py — P20 RED: Tony must verify itself.

--selftest runs the stock checks (suite, ruff, mypy, waveguard seam) and
prints one PASS/FAIL line each; exit 0 only when nothing failed. Optional
tools (ruff/mypy) report SKIP when absent — never a false PASS.

Also pins the P20 hygiene contracts:
- research.wave_cmds real mode only (sources_path is required, no legacy).
- test files are named by function, not dev phase (no test_p<digits>.py).
"""
import glob
import inspect
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def _load_tony_module():
    """Load the `tony` CLI script as a module (`tony` has no .py suffix,
    so importlib can't derive a loader — use SourceFileLoader directly)."""
    from importlib.machinery import SourceFileLoader
    return SourceFileLoader("tony_cli", os.path.join(ROOT, "tony")).load_module()


def test_cli_has_selftest_flag_wired():
    src = open(os.path.join(ROOT, "tony")).read()
    assert 'p.add_argument("--selftest"' in src
    assert "return selftest_exit(cmd_selftest())" in src
    assert "def cmd_selftest()" in src
    assert "def selftest_exit(" in src


def test_selftest_module_function_checks():
    """cmd_selftest returns list of (name, ok, detail) checks it would run."""
    tony = _load_tony_module()
    results = tony.cmd_selftest()
    names = [n for n, _ok, _d in results]
    assert "tests" in names, names
    assert "waveguard" in names, names
    # ruff/mypy optional: present or absent is fine, but no fake PASS
    for name, ok, detail in results:
        assert isinstance(ok, bool)
        if ok is False:
            assert detail, f"failing check {name} must carry detail"


def test_selftest_exits_nonzero_on_failure():
    """A failing check must propagate (exit contract is return int)."""
    tony = _load_tony_module()
    # force a failure through the seam: unknown check name in an injected list
    results = [("forced", False, "injected failure")]
    rc = tony.selftest_exit(results)
    assert rc == 1


def test_research_wave_cmds_requires_sources():
    """P20: legacy URL-count mode is gone — sources_path is required."""
    from lib import research
    sig = inspect.signature(research.wave_cmds)
    assert "sources_path" in sig.parameters
    assert sig.parameters["sources_path"].default is inspect.Parameter.empty, \
        "sources_path must be required (no legacy fallback)"


def test_test_files_named_by_function_not_phase():
    """No test_p<digits>.py files — phase numbers are ledger history, not names."""
    pattern = os.path.join(os.path.dirname(__file__), "test_p[0-9]*.py")
    offenders = [os.path.basename(p) for p in glob.glob(pattern)]
    assert not offenders, f"rename phase-named tests: {offenders}"
