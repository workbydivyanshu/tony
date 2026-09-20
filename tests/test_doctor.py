"""tests/test_doctor.py — P23 RED: pin the seam for lib/doctor.py run_all.

run_all(home, catalog_fn, mcp_fn, run_fn, which_fn) -> [(name, status, detail)]
status in {ok, warn, fail, skip}.

Every dependency is faked: temp HOME via tempfile.mkdtemp + shutil.rmtree,
fake catalog_fn/mcp_fn/run_fn/which_fn lambdas. Zero live model calls,
zero real sleep, zero real-HOME mutation, zero daemon/systemctl state changes.
"""
import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import lib.doctor  # noqa: F401 — seam pin; lib/doctor.py does not exist yet (RED)


def _fresh_home():
    """Create a temp HOME, return path; caller must shutil.rmtree in finally."""
    d = tempfile.mkdtemp(prefix="tony-doctor-")
    return d


def test_all_ok_healthy_path():
    """All components healthy -> every check returns (name, 'ok', detail)."""
    home = _fresh_home()
    try:
        os.makedirs(os.path.join(home, ".tony"), exist_ok=True)
        results = lib.doctor.run_all(
            home,
            catalog_fn=lambda: [],
            mcp_fn=lambda: [],
            run_fn=lambda cmd: 0,
            which_fn=lambda name: "/usr/bin/true",
        )
        assert results, "healthy path must return non-empty results"
        for name, status, detail in results:
            assert status in ("ok", "warn", "fail", "skip"), f"bad status {status!r} for {name}"
            if status == "ok":
                assert detail, f"ok status for {name} must carry detail"
    finally:
        shutil.rmtree(home)


def test_binary_missing_fail():
    """opencode binary absent -> check returns ('opencode_bin', 'fail', detail)."""
    home = _fresh_home()
    try:
        os.makedirs(os.path.join(home, ".tony"), exist_ok=True)
        results = lib.doctor.run_all(
            home,
            catalog_fn=lambda: [],
            mcp_fn=lambda: [],
            run_fn=lambda cmd: 0,
            which_fn=lambda name: None,
        )
        fails = [(n, s, d) for n, s, d in results if s == "fail"]
        assert fails, "missing binary must produce at least one fail"
        assert any("opencode" in n.lower() or "binary" in d.lower() for n, s, d in fails), \
            f"fail detail must mention binary; got {fails}"
    finally:
        shutil.rmtree(home)


def test_catalog_fn_raises_or_empty_fail():
    """catalog_fn raises or returns empty -> ('catalog', 'fail', detail)."""
    home = _fresh_home()
    try:
        os.makedirs(os.path.join(home, ".tony"), exist_ok=True)
        # catalog_fn raises
        results = lib.doctor.run_all(
            home,
            catalog_fn=lambda: (_ for _ in ()).throw(RuntimeError("catalog down")),
            mcp_fn=lambda: [],
            run_fn=lambda cmd: 0,
            which_fn=lambda name: "/usr/bin/true",
        )
        fails = [(n, s, d) for n, s, d in results if s == "fail"]
        assert fails, "catalog_fn raise must produce fail"
        assert any("catalog" in n.lower() or "catalog" in d.lower() for n, s, d in fails), \
            f"fail detail must mention catalog; got {fails}"
    finally:
        shutil.rmtree(home)


def test_run_fn_file_not_found_skip():
    """run_fn raising FileNotFoundError -> ('daemon', 'skip', detail).

    Never fake PASS for a missing systemctl/daemon binary.
    """
    home = _fresh_home()
    try:
        os.makedirs(os.path.join(home, ".tony"), exist_ok=True)
        results = lib.doctor.run_all(
            home,
            catalog_fn=lambda: [],
            mcp_fn=lambda: [],
            run_fn=lambda cmd: (_ for _ in ()).throw(FileNotFoundError("no systemctl")),
            which_fn=lambda name: "/usr/bin/true",
        )
        skips = [(n, s, d) for n, s, d in results if s == "skip"]
        assert skips, "FileNotFoundError in run_fn must produce skip"
        assert any("systemctl" in d.lower() or "daemon" in n.lower() for n, s, d in skips), \
            f"skip detail must mention systemctl/daemon; got {skips}"
    finally:
        shutil.rmtree(home)


def test_unit_installed_but_inactive_warn():
    """Unit installed but nonzero returncode -> ('daemon', 'warn', detail)."""
    home = _fresh_home()
    try:
        os.makedirs(os.path.join(home, ".tony"), exist_ok=True)
        # which_fn finds the unit, but run_fn returns nonzero (inactive)
        results = lib.doctor.run_all(
            home,
            catalog_fn=lambda: [],
            mcp_fn=lambda: [],
            run_fn=lambda cmd: 1,
            which_fn=lambda name: "/usr/bin/systemctl",
        )
        warns = [(n, s, d) for n, s, d in results if s == "warn"]
        assert warns, "nonzero returncode must produce warn"
        assert any("inactive" in d.lower() or "daemon" in n.lower() for n, s, d in warns), \
            f"warn detail must mention inactive/daemon; got {warns}"
    finally:
        shutil.rmtree(home)


def test_bad_cron_names_job_fail():
    """Bad cron name in schedule -> ('schedule', 'fail', detail)."""
    home = _fresh_home()
    try:
        os.makedirs(os.path.join(home, ".tony"), exist_ok=True)
        results = lib.doctor.run_all(
            home,
            catalog_fn=lambda: [],
            mcp_fn=lambda: [],
            run_fn=lambda cmd: 0,
            which_fn=lambda name: "/usr/bin/true",
        )
        fails = [(n, s, d) for n, s, d in results if s == "fail"]
        assert fails, "bad cron must produce fail"
        assert any("cron" in d.lower() or "schedule" in n.lower() for n, s, d in fails), \
            f"fail detail must mention cron/schedule; got {fails}"
    finally:
        shutil.rmtree(home)


def test_corrupt_ledger_warn():
    """Corrupt schedule-ledger.json -> ('ledger', 'warn', detail)."""
    home = _fresh_home()
    try:
        tony_dir = os.path.join(home, ".tony")
        os.makedirs(tony_dir, exist_ok=True)
        # Write corrupt ledger
        with open(os.path.join(tony_dir, "schedule-ledger.json"), "w") as f:
            f.write("{bad json!!!")
        results = lib.doctor.run_all(
            home,
            catalog_fn=lambda: [],
            mcp_fn=lambda: [],
            run_fn=lambda cmd: 0,
            which_fn=lambda name: "/usr/bin/true",
        )
        warns = [(n, s, d) for n, s, d in results if s == "warn"]
        assert warns, "corrupt ledger must produce warn"
        assert any("ledger" in d.lower() or "corrupt" in d.lower() for n, s, d in warns), \
            f"warn detail must mention ledger/corrupt; got {warns}"
    finally:
        shutil.rmtree(home)


def test_present_but_unwritable_home_fail():
    """Home dir exists but not writable -> ('home', 'fail', detail)."""
    home = _fresh_home()
    try:
        os.makedirs(os.path.join(home, ".tony"), exist_ok=True)
        # Make home unwritable
        os.chmod(home, 0o444)
        results = lib.doctor.run_all(
            home,
            catalog_fn=lambda: [],
            mcp_fn=lambda: [],
            run_fn=lambda cmd: 0,
            which_fn=lambda name: "/usr/bin/true",
        )
        fails = [(n, s, d) for n, s, d in results if s == "fail"]
        assert fails, "unwritable home must produce fail"
        assert any("home" in n.lower() or "writ" in d.lower() for n, s, d in fails), \
            f"fail detail must mention home/writable; got {fails}"
    finally:
        os.chmod(home, 0o755)
        shutil.rmtree(home)


def test_fresh_machine_absent_paths_ok():
    """Fresh machine with absent-but-creatable ~/.tony paths must NOT fail.

    Absent paths are detail/ok, never fail — doctor should create them.
    """
    home = _fresh_home()
    try:
        # Do NOT create .tony — simulate fresh machine
        results = lib.doctor.run_all(
            home,
            catalog_fn=lambda: [],
            mcp_fn=lambda: [],
            run_fn=lambda cmd: 0,
            which_fn=lambda name: "/usr/bin/true",
        )
        fails = [(n, s, d) for n, s, d in results if s == "fail"]
        assert not fails, f"fresh machine must not fail; got {fails}"
        # Absent-but-creatable paths should be ok or skip with detail
        for n, s, d in results:
            assert s in ("ok", "skip"), f"fresh-machine path {n} must be ok/skip, got {s}"
            assert d, f"fresh-machine path {n} must carry detail"
    finally:
        shutil.rmtree(home)


def test_cli_has_doctor_flag_wired():
    """Source pin: tony must have --doctor flag, cmd_doctor def, and dispatch."""
    src = open(os.path.join(os.path.dirname(__file__), "..", "tony")).read()
    assert 'p.add_argument("--doctor"' in src, "missing --doctor flag in argparse"
    assert "def cmd_doctor()" in src, "missing cmd_doctor function"
    assert "cmd_doctor()" in src, "missing cmd_doctor dispatch call"
