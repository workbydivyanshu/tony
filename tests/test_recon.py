"""tests/test_recon.py — P37 recon-first planning units.

lib/recon.py run_recon_phase(role_call_fn, explorer_model, workdir,
mission, angles) is pure orchestration over an injected role_call_fn:
no subprocess, no models, no disk. Fakes record call order + script
findings. Zero live burn.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib import recon


def _fake_runner_factory(script):
    """role_call_fn fake: records (role, subtask) calls, returns scripted
    outputs in order; raises RuntimeError('boom') on 'RAISE' entries."""
    calls = []

    def fake(role, subtask):
        calls.append((role, subtask))
        out = script[min(len(calls) - 1, len(script) - 1)]
        if out == "RAISE":
            raise RuntimeError("boom")
        return out

    fake.calls = calls
    return fake


def test_recon_runs_three_angles_before_anything():
    """Three explorer calls (layout, files, risks) with mission+workdir."""
    fake = _fake_runner_factory(["LAYOUT", "FILES", "RISKS"])
    out = recon.run_recon_phase(fake, "m1", "/x/repo", "add login page")
    assert out == ["LAYOUT", "FILES", "RISKS"], out
    assert len(fake.calls) == 3, fake.calls
    assert all(r == "explorer" for r, _ in fake.calls), fake.calls
    assert all("add login page" in s and "/x/repo" in s for _, s in fake.calls), fake.calls


def test_recon_failure_never_kills_mission():
    """A blowing explorer yields [] for its slot; phase still returns."""
    fake = _fake_runner_factory(["LAYOUT", "RAISE", "RISKS"])
    out = recon.run_recon_phase(fake, "m1", "/x/repo", "add login page")
    assert out == ["LAYOUT", "RISKS"], out


def test_recon_empty_angles_no_calls():
    """angles=0 -> [] with zero role calls (flag-off path)."""
    fake = _fake_runner_factory([])
    out = recon.run_recon_phase(fake, "m1", "/x/repo", "add login page",
                                angles=0)
    assert out == [], out
    assert fake.calls == [], fake.calls


def test_architect_prompt_carries_recon_lines():
    """recon_lines inject a RECON section; default output unchanged."""
    from lib import roles
    base = roles.architect_prompt("do X")
    explicit = roles.architect_prompt("do X", recon_lines=None)
    assert base == explicit, "default must equal recon_lines=None"
    assert "RECON" not in base, base[-200:]
    injected = roles.architect_prompt("do X", recon_lines=["LAYOUT map"])
    assert "LAYOUT map" in injected, injected[-300:]
    assert "RECON" in injected, injected[-300:]
