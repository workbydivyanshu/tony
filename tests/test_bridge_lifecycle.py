"""tests/test_bridge_lifecycle.py — H1 T3 bridge lifecycle pins.

Tests cmd_bridge_start and _check_bridge with fake run fns.
Zero daemon spawn. Temp HOME isolation for disk-touching paths.
"""
import os
import sys
import tempfile
import shutil
from importlib.machinery import SourceFileLoader

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import lib.doctor  # noqa: F401

# Import tony as a module (script file without .py extension)
_tony_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tony"))
tony = SourceFileLoader("tony", _tony_path).load_module()  # type: ignore[attr-defined]
cmd_bridge_start = tony.cmd_bridge_start  # noqa: E402


def _fake_run_success(cmd, **kwargs):
    """Fake run_fn: simulates kimi-webbridge status returning 0."""
    assert cmd[0].endswith("kimi-webbridge"), f"unexpected cmd: {cmd}"
    assert cmd[1] == "status"
    class _R:
        returncode = 0
        stdout = "ok"
        stderr = ""
    return _R()


def _fake_run_failure(cmd, **kwargs):
    """Fake run_fn: simulates kimi-webbridge status returning non-zero."""
    assert cmd[0].endswith("kimi-webbridge"), f"unexpected cmd: {cmd}"
    assert cmd[1] == "status"
    class _R:
        returncode = 1
        stdout = ""
        stderr = "not running"
    return _R()


def test_bridge_up_returns_ok():
    """bridge up (rc=0) -> ('bridge', 'ok', detail)."""
    home = tempfile.mkdtemp(prefix="tony-bridge-")
    try:
        bridge_bin = os.path.join(home, "kimi-webbridge")
        open(bridge_bin, "w").close()
        os.chmod(bridge_bin, 0o755)
        results = lib.doctor.run_all(
            home,
            catalog_fn=lambda: [],
            mcp_fn=lambda: [],
            run_fn=_fake_run_success,
            which_fn=lambda name: None,
            bridge_path=bridge_bin,
        )
        bridge = [r for r in results if r[0] == "bridge"]
        assert bridge, "bridge check must be present"
        assert bridge[0][1] == "ok", f"expected ok, got {bridge[0]}"
        assert "reachable" in bridge[0][2].lower()
    finally:
        shutil.rmtree(home)


def test_bridge_down_returns_warn():
    """bridge down (rc!=0) -> ('bridge', 'warn', detail with start command)."""
    home = tempfile.mkdtemp(prefix="tony-bridge-")
    try:
        bridge_bin = os.path.join(home, "kimi-webbridge")
        open(bridge_bin, "w").close()
        os.chmod(bridge_bin, 0o755)
        results = lib.doctor.run_all(
            home,
            catalog_fn=lambda: [],
            mcp_fn=lambda: [],
            run_fn=_fake_run_failure,
            which_fn=lambda name: None,
            bridge_path=bridge_bin,
        )
        bridge = [r for r in results if r[0] == "bridge"]
        assert bridge, "bridge check must be present"
        assert bridge[0][1] == "warn", f"expected warn, got {bridge[0]}"
        assert "kimi-webbridge start" in bridge[0][2], \
            f"detail must name start command; got {bridge[0][2]}"
    finally:
        shutil.rmtree(home)


def test_bridge_absent_skip():
    """Binary absent -> ('bridge', 'skip', detail). Never fail."""
    home = tempfile.mkdtemp(prefix="tony-bridge-")
    try:
        # Do NOT create the binary — simulate fresh machine
        results = lib.doctor.run_all(
            home,
            catalog_fn=lambda: [],
            mcp_fn=lambda: [],
            run_fn=_fake_run_success,
            which_fn=lambda name: None,
            bridge_path=os.path.join(home, "nonexistent", "kimi-webbridge"),
        )
        bridge = [r for r in results if r[0] == "bridge"]
        assert bridge, "bridge check must be present"
        assert bridge[0][1] == "skip", f"expected skip, got {bridge[0]}"
    finally:
        shutil.rmtree(home)


def test_probe_never_spawns():
    """Source pin: cmd_bridge_start calls subprocess directly;
    status()/read paths contain no spawn. Verify no implicit daemon spawn."""
    src = open(os.path.join(os.path.dirname(__file__), "..", "lib", "kimi.py")).read()
    # kimi.py must not spawn the daemon implicitly
    assert "subprocess" not in src, "kimi.py must not use subprocess (no implicit spawn)"
    assert "Popen" not in src, "kimi.py must not use Popen"
    # cmd_bridge_start uses subprocess but only on explicit --bridge-start
    tony_src = open(os.path.join(os.path.dirname(__file__), "..", "tony")).read()
    assert "cmd_bridge_start" in tony_src, "cmd_bridge_start must exist"
    assert "--bridge-start" in tony_src, "--bridge-start flag must exist"
