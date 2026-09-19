"""tests/test_p16.py — P16 RED: latency pin must capture today's slow lane honestly."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_callshape_module():
    from lib import callshape  # noqa: F401


def test_wallclock_and_internal_steps():
    from lib import callshape
    import subprocess
    # seam proof only: a stub runner's duration + captured argv shape.
    argv, dt = callshape.timed_run(["echo", "hi"])
    assert argv == ["echo", "hi"] and dt >= 0
    text = subprocess.run(["echo", "hi"], capture_output=True, text=True).stdout
    steps = callshape.count_internal_steps(text)
    assert steps == 0, text