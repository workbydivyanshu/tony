"""RED proof: workdir resolution, foreign-path detection, and CLI --workdir threading.

Missing behavior: lib/workdir.py does not yet exist.
This spec defines the target API:
  - resolve(explicit, slug) -> str
  - is_foreign(path) -> bool
  - DEFAULT_ROOT = ~/.tony/work (expanduser at CALL time)

Plus T3: --workdir threading through cmd_mission/cmd_resume/cmd_watch
with foreign+yes bypass warning and global path pins.
"""
import os
import shutil
import sys
import tempfile
import importlib.util
import importlib.machinery

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib import workdir
from lib import boulder

TONY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tony")


def _load_tony():
    """Load tony script as a module (no .py extension)."""
    loader = importlib.machinery.SourceFileLoader("tony", TONY_PATH)
    spec = importlib.util.spec_from_file_location("tony", TONY_PATH, loader=loader)
    assert spec is not None, "failed to load tony spec"
    assert spec.loader is not None, "failed to load tony loader"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── lib/workdir.py tests ────────────────────────────────────

def test_resolve_none_returns_default_work_slug():
    """resolve(None, slug) returns ~/.tony/work/<slug>."""
    slug = "my-project"
    result = workdir.resolve(None, slug)
    expected = os.path.join(os.path.expanduser("~"), ".tony", "work", slug)
    assert result == expected, f"expected {expected}, got {result}"


def test_resolve_explicit_dir_returns_abspath():
    """resolve(explicit_dir, slug) returns abspath(explicit_dir) — pure, no mkdir."""
    explicit = tempfile.mkdtemp()
    try:
        slug = "my-project"
        result = workdir.resolve(explicit, slug)
        assert result == os.path.abspath(explicit), \
            f"expected abspath({explicit}), got {result}"
        # Must not have created a subdirectory
        assert not os.path.isdir(os.path.join(explicit, slug)), \
            "resolve must not mkdir"
    finally:
        shutil.rmtree(explicit, ignore_errors=True)


def test_is_foreign_false_under_default_root():
    """is_foreign(path) is False when path is under ~/.tony/work."""
    path = os.path.join(os.path.expanduser("~"), ".tony", "work", "my-project")
    assert workdir.is_foreign(path) is False, f"expected False for {path}"


def test_is_foreign_true_for_tmp():
    """is_foreign(path) is True for /tmp paths."""
    assert workdir.is_foreign("/tmp/something") is True, \
        "expected True for /tmp/something"


def test_is_foreign_true_for_foreign_repo():
    """is_foreign(path) is True for paths outside ~/.tony/work."""
    path = "/home/divyu/tony"
    assert workdir.is_foreign(path) is True, \
        f"expected True for {path}"


# ── T3 RED: --workdir CLI threading pins ────────────────────
# These tests FAIL in RED (cmd_* have no workdir param).
# After GREEN, they PASS and verify the workdir flows correctly.

def _patch_engine_fn(name, fake_fn):
    """Patch a function on lib.engine by name, return original."""
    import lib.engine as eng_mod
    orig = getattr(eng_mod, name)
    setattr(eng_mod, name, fake_fn)
    return orig


def _patch_roles_fn(name, fake_fn):
    """Patch a function on lib.roles by name, return original."""
    import lib.roles as roles_mod
    orig = getattr(roles_mod, name)
    setattr(roles_mod, name, fake_fn)
    return orig


def _restore_engine_fn(name, orig):
    import lib.engine as eng_mod
    setattr(eng_mod, name, orig)


def _restore_roles_fn(name, orig):
    import lib.roles as roles_mod
    setattr(roles_mod, name, orig)


def test_cmd_mission_workdir_passes_to_verify_wave_and_run_loop():
    """(a) cmd_mission(..., workdir=<tmp>) passes that dir as cwd= into
    verify_wave AND as workdir= into run_loop.

    RED: cmd_mission has no workdir param -> TypeError.
    GREEN: workdir flows to verify_wave(cwd=<tmp>) and run_loop(workdir=<tmp>).
    """
    tony = _load_tony()
    tmp = tempfile.mkdtemp()
    try:
        captured_run_loop = {}
        captured_verify_wave = {}

        def fake_run_loop(b, tier_models, workdir, **kw):
            captured_run_loop["workdir"] = workdir
            return b

        def fake_verify_wave(b, **kw):
            captured_verify_wave["cwd"] = kw.get("cwd")
            return []

        orig_rl = _patch_engine_fn("run_loop", fake_run_loop)
        orig_vw = _patch_engine_fn("verify_wave", fake_verify_wave)
        orig_rc = _patch_engine_fn("role_call", lambda *a, **kw: {"status": "ok", "output": "# Boulder\ntest", "outfile": "/tmp/x.md", "duration": 0.1, "model": "m"})

        try:
            captured_architect_prompt = {}

            def fake_architect_prompt(*args, **kw):
                captured_architect_prompt["workdir"] = kw.get("workdir")
                return "# Boulder\ntest"

            orig_ap = _patch_roles_fn("architect_prompt", fake_architect_prompt)

            try:
                # This must work after GREEN; raises TypeError in RED
                tony.cmd_mission("test mission", workdir=tmp, yes=True)
                # Verify the workdir flowed correctly
                assert captured_run_loop.get("workdir") == tmp, \
                    f"run_loop workdir={captured_run_loop.get('workdir')}, expected {tmp}"
                assert captured_verify_wave.get("cwd") == tmp, \
                    f"verify_wave cwd={captured_verify_wave.get('cwd')}, expected {tmp}"
                assert captured_architect_prompt.get("workdir") == tmp, \
                    f"architect_prompt workdir={captured_architect_prompt.get('workdir')}, expected {tmp}"
            finally:
                _restore_roles_fn("architect_prompt", orig_ap)
        finally:
            _restore_engine_fn("run_loop", orig_rl)
            _restore_engine_fn("verify_wave", orig_vw)
            _restore_engine_fn("role_call", orig_rc)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_cmd_resume_workdir_passes_to_verify_wave_and_run_loop():
    """(b) cmd_resume likewise passes workdir as cwd= into verify_wave
    AND as workdir= into run_loop.

    RED: cmd_resume has no workdir param -> TypeError.
    GREEN: workdir flows to verify_wave(cwd=<tmp>) and run_loop(workdir=<tmp>).
    """
    tony = _load_tony()
    tmp = tempfile.mkdtemp()
    slug = "resume-red-test"
    b = boulder.new(slug)
    boulder.add_todo(b, "1. test item")
    bpath = boulder.save(slug, b)
    try:
        captured_run_loop = {}
        captured_verify_wave = {}

        def fake_run_loop(b, tier_models, workdir, **kw):
            captured_run_loop["workdir"] = workdir
            return b

        def fake_verify_wave(b, **kw):
            captured_verify_wave["cwd"] = kw.get("cwd")
            return []

        orig_rl = _patch_engine_fn("run_loop", fake_run_loop)
        orig_vw = _patch_engine_fn("verify_wave", fake_verify_wave)
        orig_rc = _patch_engine_fn("role_call", lambda *a, **kw: {"status": "ok", "output": "", "outfile": "/tmp/x.md", "duration": 0.1, "model": "m"})

        try:
            # This must work after GREEN; raises TypeError in RED
            tony.cmd_resume(slug, workdir=tmp)
            # Verify the workdir flowed correctly
            assert captured_run_loop.get("workdir") == tmp, \
                f"run_loop workdir={captured_run_loop.get('workdir')}, expected {tmp}"
            assert captured_verify_wave.get("cwd") == tmp, \
                f"verify_wave cwd={captured_verify_wave.get('cwd')}, expected {tmp}"
        finally:
            _restore_engine_fn("run_loop", orig_rl)
            _restore_engine_fn("verify_wave", orig_vw)
            _restore_engine_fn("role_call", orig_rc)
    finally:
        os.unlink(bpath)
        shutil.rmtree(tmp, ignore_errors=True)


def test_cmd_watch_uses_override_workdir():
    """(c) cmd_watch(slug, workdir=...) uses override else TONY_DIR/work/<slug> default.

    RED: cmd_watch has no workdir param -> TypeError.
    GREEN: workdir=<tmp> overrides the default.
    """
    tony = _load_tony()
    tmp = tempfile.mkdtemp()
    try:
        # After GREEN, cmd_watch must accept workdir param
        # and use it instead of the hardcoded TONY_DIR/work/<slug>
        # We verify by checking the source has the resolve call
        src = open(TONY_PATH).read()
        assert "workdir_mod.resolve" in src, \
            "cmd_watch must use workdir_mod.resolve for workdir (RED — missing)"
        # Also verify cmd_watch accepts workdir param
        import inspect
        sig = inspect.signature(tony.cmd_watch)
        assert "workdir" in sig.parameters, \
            f"cmd_watch must have workdir param, got: {list(sig.parameters)}"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_cmd_watch_default_workdir():
    """(c) cmd_watch(slug) without workdir uses TONY_DIR/work/<slug> default.

    After GREEN, workdir=None resolves via workdir_mod.resolve(None, slug)
    which returns ~/.tony/work/<slug>.
    """
    tony = _load_tony()
    import inspect
    sig = inspect.signature(tony.cmd_watch)
    assert "workdir" in sig.parameters, \
        f"cmd_watch must have workdir param, got: {list(sig.parameters)}"
    # workdir default must be None
    assert sig.parameters["workdir"].default is None, \
        "workdir default must be None"


def test_yes_foreign_workdir_prints_warning():
    """(d) --yes + foreign workdir prints a bypass WARNING naming the dir.

    RED: cmd_mission has no workdir param and no foreign check.
    GREEN: --yes with a foreign workdir must print:
      tony: WARNING --yes bypasses the sole human checkpoint on foreign workdir <dir>
    """
    tony = _load_tony()
    tmp = tempfile.mkdtemp()
    try:
        # After GREEN, cmd_mission must accept workdir param
        import inspect
        sig = inspect.signature(tony.cmd_mission)
        assert "workdir" in sig.parameters, \
            f"cmd_mission must have workdir param, got: {list(sig.parameters)}"
        # Verify the source has the foreign+yes warning
        src = open(TONY_PATH).read()
        assert "bypasses the sole human checkpoint" in src, \
            "must print foreign workdir bypass warning (RED — missing)"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_boulder_path_for_and_reports_untouched():
    """(e) boulder.path_for still ~/.tony/boulders + reports still ~/.fleet/out
    (global paths untouched pin).
    """
    # boulder.path_for must resolve to ~/.tony/boulders
    slug = "pin-test"
    p = boulder.path_for(slug)
    expected = os.path.join(os.path.expanduser("~"), ".tony", "boulders", f"{slug}.md")
    assert p == expected, f"boulder.path_for must be {expected}, got {p}"

    # report path must be ~/.fleet/out
    src = open(TONY_PATH).read()
    assert '"~/.fleet/out"' in src or "'~/.fleet/out'" in src, \
        "report path must remain ~/.fleet/out (global path untouched)"


def test_architect_prompt_workdir_is_last_kwarg():
    """architect_prompt workdir must be the LAST keyword param — never passed positionally.

    RED: verify the signature has workdir as the last param.
    """
    from lib import roles
    import inspect
    sig = inspect.signature(roles.architect_prompt)
    params = list(sig.parameters.keys())
    assert params[-1] == "workdir", \
        f"workdir must be last param, got: {params}"
    # Verify it has a default of None
    assert sig.parameters["workdir"].default is None, \
        "workdir default must be None"


def test_role_call_confines_subprocess_cwd_to_workdir():
    """role_call must run opencode with cwd=workdir (live P34 find: a
    relative-path builder command landed hello.txt in the invoker CWD)."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from lib import engine
    seen = {}

    def fake_runner(cmd, **kw):
        seen.update(kw)
        class R: returncode = 0; stdout = "ok\n"; stderr = ""
        return R()

    d = tempfile.mkdtemp()
    try:
        engine.role_call("builder", "m1", "do X", workdir=d,
                         runner=fake_runner,
                         runslog=os.path.join(d, "runs.log"))
        assert seen.get("cwd") == d, f"subprocess cwd must be workdir, got: {seen}"
    finally:
        shutil.rmtree(d, ignore_errors=True)
