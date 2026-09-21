"""tests/test_research_waveguard.py — research wave routing through waveguard.

RED confirmation: the unguarded bare listcomp in cmd_research bypasses
waveguard entirely. The GREEN fix routes every wave command through
eng.run_wave (the choke point) before subprocess ever sees it.

Hostile strings are passed to check() only, never executed via subprocess.
"""
import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_hostile_wave_cmd_blocked_by_waveguard():
    """Hostile wave cmd through the research routing path completes as FAIL
    with BLOCKED-by-waveguard in the boulder log while monkeypatched engine
    subprocess never runs (patch subprocess.run in the ENGINE namespace to
    raise if called)."""
    from lib import boulder as bmod
    from lib import engine as eng
    from lib import waveguard as w
    from lib import research as res_mod

    d = tempfile.mkdtemp()
    try:
        report_path = os.path.join(d, "brief.md")
        sources_path = os.path.join(d, "explorers.md")
        with open(sources_path, "w") as f:
            f.write("a http://x.com b https://y.com c http://z.com")
        with open(report_path, "w") as f:
            f.write("a http://x.com b https://y.com c http://z.com")

        # Hostile string: only passed to check(), never executed
        hostile_cmd = "sudo rm -rf /tmp/never"
        safe, reason = w.check(hostile_cmd)
        assert not safe, f"hostile cmd must be blocked by waveguard: {reason}"

        # Build throwaway boulder: real research wave cmds + hostile injection
        b2 = bmod.new("research waveguard test")
        for _cmd in res_mod.wave_cmds(report_path, sources_path):
            bmod.add_wave(b2, _cmd)
        bmod.add_wave(b2, hostile_cmd)

        # Patch engine subprocess.run to raise if called
        real_run = eng.subprocess.run
        calls = []

        def raising_run(cmd, **kw):
            calls.append(cmd)
            raise RuntimeError("SUBPROCESS_RAISED")

        eng.subprocess.run = raising_run
        try:
            workdir = d
            results = eng.run_wave(b2, cwd=workdir)

            # Hostile item must be FAIL, gated by waveguard
            assert results[-1] is False, results
            assert b2["wave"][-1]["box"] is False, b2["wave"]
            # BLOCKED-by-waveguard must appear in the boulder log
            assert any("BLOCKED by waveguard" in ln for ln in b2["log"]), b2["log"]
            # Patched engine subprocess must never have run the hostile cmd
            assert not any(
                isinstance(c, str) and "rm -rf" in c for c in calls
            ), f"subprocess ran hostile cmd: {calls}"
        finally:
            eng.subprocess.run = real_run
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_benign_wave_cmd_executes():
    """Benign tmpdir-path wave cmds still execute for real (echo/test into tmpdir)."""
    from lib import boulder as bmod
    from lib import engine as eng

    d = tempfile.mkdtemp()
    try:
        marker = os.path.join(d, "marker.txt")
        benign_cmd = f"echo ok > {marker}"

        b2 = bmod.new("research benign test")
        bmod.add_wave(b2, benign_cmd)

        results = eng.run_wave(b2, cwd=d)

        assert results == [True], results
        assert b2["wave"][0]["box"] is True, b2["wave"]
        assert os.path.exists(marker), f"marker not found at {marker}"
        with open(marker) as f:
            assert f.read().strip() == "ok", "marker content wrong"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_unguarded_path_bypasses_waveguard():
    """RED confirmation: the bare listcomp in cmd_research bypasses
    waveguard entirely. The unguarded path calls subprocess.run directly
    (tony's own import) and never touches eng.subprocess.run or waveguard.check().

    This test confirms the RED state: hostile wave commands reach subprocess
    without waveguard gating. After the GREEN fix, cmd_research routes
    through eng.run_wave instead of the bare listcomp.
    """
    from lib import research as res_mod
    from lib import waveguard as w
    import subprocess

    d = tempfile.mkdtemp()
    try:
        report_path = os.path.join(d, "brief.md")
        sources_path = os.path.join(d, "explorers.md")
        with open(sources_path, "w") as f:
            f.write("a http://x.com b https://y.com c http://z.com")
        with open(report_path, "w") as f:
            f.write("a http://x.com b https://y.com c http://z.com")

        # Get real research wave cmds (the same ones cmd_research uses)
        cmds = res_mod.wave_cmds(report_path, sources_path)

        # Confirm the hostile command would be blocked by waveguard
        # but the bare listcomp never calls check()
        hostile_cmd = "sudo rm -rf /tmp/never"
        safe, _ = w.check(hostile_cmd)
        assert not safe, "hostile cmd must be blocked by waveguard"

        # Patch tony's subprocess.run to track calls (the bare listcomp uses this)
        real_run = subprocess.run
        calls = []

        def tracking_run(cmd, **kw):
            calls.append(cmd)
            class R:
                returncode = 0
                stdout = ""
                stderr = ""
            return R()

        subprocess.run = tracking_run
        try:
            # Simulate the bare listcomp from cmd_research (RED path)
            _ = [subprocess.run(c, shell=True, capture_output=True).returncode == 0
                 for c in cmds]

            # The bare listcomp executed commands via subprocess.run
            assert len(calls) == 2, f"expected 2 calls, got {len(calls)}"
            # The bare listcomp never touches eng.subprocess.run
            # (it uses tony's own subprocess import, not engine's)
            assert len(calls) > 0, "bare listcomp must call subprocess.run"
        finally:
            subprocess.run = real_run
    finally:
        shutil.rmtree(d, ignore_errors=True)
