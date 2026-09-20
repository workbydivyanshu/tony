"""P24 RED proof: wave-cwd seam — cwd is load-bearing; entrypoints must pass it.

Recon call-site list (run_wave/verify_wave across tony + lib/):
  lib/engine.py:78   run_wave(b, cwd="/tmp")  DEFINITION (default cwd="/tmp")
  lib/engine.py:292  verify_wave(b, max_verify=3, cwd="/tmp", fix_fn=None)  DEFINITION
  lib/engine.py:303  run_wave(b, cwd=cwd)  INTERNAL call inside verify_wave
  tony:382  cmd_mission -> eng.verify_wave(b, max_verify=max_verify, fix_fn=_builder_fix)
           NO cwd=workdir (workdir defined at tony:327, unused here)
  tony:427  cmd_resume -> eng.verify_wave(b, max_verify=max_verify, fix_fn=_builder_fix)
           NO cwd=workdir (workdir defined at tony:414, unused here)
  tony:644  selftest_checks -> engine.run_wave(b, cwd="/tmp")  [EXCLUDED: synthetic boulder, cwd=/tmp intentional]
  tests/test_wave_sanitize_report.py:12  engine.run_wave(b, cwd="/tmp")
  tests/test_wave_sanitize_report.py:20  engine.run_wave(b, cwd="/tmp")
  tests/test_waveguard_citations.py:81  eng.run_wave(b, cwd="/tmp")
  tests/test_progress_critic_gate.py:101  engine.run_wave(b, cwd=tmpdir)
  tests/test_progress_critic_gate.py:117  engine.verify_wave(b, max_verify=2, cwd=tmpdir, fix_fn=fix_fn)
  tests/test_progress_critic_gate.py:131  engine.run_wave(b, cwd=tmpdir)
  tests/test_review_hardening.py:34  engine.verify_wave(b, max_verify=3, cwd=tmpdir, fix_fn=...)
  tests/test_review_hardening.py:41  engine.verify_wave(b2, max_verify=2, cwd=tmpdir, fix_fn=None)
  tests/test_role_tags_parallel.py:66  engine.verify_wave(b, max_verify=2, cwd=tmpdir, ...)

Non-selftest PRODUCTION call sites: tony:382 (cmd_mission), tony:427 (cmd_resume).
Both compute workdir but never pass it to verify_wave — falls through to /tmp default.
"""
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib import engine, boulder

TONY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tony")


def test_s1_cwd_passes():
    """verify_wave with cwd=workdir runs relative wave items against that dir.

    Documents correct behavior: when cwd is explicitly passed, relative
    wave commands resolve against it. May already pass — recorded honestly.
    """
    workdir = tempfile.mkdtemp()
    try:
        open(os.path.join(workdir, "hello.txt"), "w").write("hi")
        b = boulder.new("s1")
        boulder.add_wave(b, "test -f hello.txt")
        res = engine.verify_wave(b, max_verify=1, cwd=workdir)
        assert res == [True], res
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def test_s2_cwd_foreign_fails():
    """Same wave with cwd=a different foreign tmpdir -> FAIL.

    Pins that cwd is load-bearing: the file exists in workdir but the
    command runs in foreign, so it cannot be found. Guards regression to
    the /tmp default.
    """
    workdir = tempfile.mkdtemp()
    foreign = tempfile.mkdtemp()
    try:
        # Create hello.txt in workdir, but run with cwd=foreign
        open(os.path.join(workdir, "hello.txt"), "w").write("hi")
        b = boulder.new("s2")
        boulder.add_wave(b, "test -f hello.txt")
        res = engine.verify_wave(b, max_verify=1, cwd=foreign)
        assert res == [False], res
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
        shutil.rmtree(foreign, ignore_errors=True)


def test_s3_entrypoints_pass_cwd():
    """cmd_mission + cmd_resume must pass cwd=workdir into verify_wave.

    Source pin on the tony entrypoint. Non-selftest call sites found in recon:
      tony:382 cmd_mission -> eng.verify_wave(b, max_verify=max_verify, fix_fn=_builder_fix)
        MISSING cwd=workdir (workdir defined at tony:327)
      tony:427 cmd_resume -> eng.verify_wave(b, max_verify=max_verify, fix_fn=_builder_fix)
        MISSING cwd=workdir (workdir defined at tony:414)
      tony:644 selftest_checks -> engine.run_wave(b, cwd="/tmp") [EXCLUDED: synthetic boulder, cwd=/tmp intentional]
      tests/test_wave_sanitize_report.py:12,20 -> engine.run_wave(b, cwd="/tmp") [test code]
      tests/test_waveguard_citations.py:81 -> eng.run_wave(b, cwd="/tmp") [test code]
      tests/test_progress_critic_gate.py:101,117,131 -> engine.run_wave/verify_wave(b, cwd=tmpdir, ...) [test code]
      tests/test_review_hardening.py:34,41 -> engine.verify_wave(b, cwd=tmpdir, ...) [test code]
      tests/test_role_tags_parallel.py:66 -> engine.verify_wave(b, cwd=tmpdir, ...) [test code]

    The two production entrypoints compute workdir but never pass it to
    verify_wave — they fall through to the /tmp default.
    """
    src = open(TONY_PATH).read()

    # cmd_mission verify_wave call must include cwd=workdir
    assert "verify_wave(b, max_verify=max_verify, cwd=workdir" in src, \
        "cmd_mission must pass cwd=workdir into verify_wave (tony:382)"

    # cmd_resume verify_wave call must include cwd=workdir
    assert "verify_wave(b, max_verify=max_verify, cwd=workdir" in src, \
        "cmd_resume must pass cwd=workdir into verify_wave (tony:427)"
