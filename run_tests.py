#!/usr/bin/env python3
"""run_tests.py — stdlib plain-assert test runner for Tony.

Tony's suite is plain-assert functions (pytest is deliberately not a
dependency). This is the stock entrypoint so a fresh clone verifies with:

    python3 run_tests.py            # full suite
    python3 run_tests.py tests/test_p19.py   # one file
"""
import glob
import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)


def _expand(args: list[str]) -> list[str]:
    """Resolve CLI args to test paths; --skip-self drops test_selftest.py.

    --skip-self exists for one reason: `tony --selftest` runs run_tests.py
    from INSIDE the suite (via test_selftest's cmd_selftest check), which
    teams up with other tests to recurse. The runner self-verifies its own
    entrypoint at startup instead (see _self_check), so the suite stays a DAG.
    """
    paths = [a for a in args if a != "--skip-self"]
    skip = "--skip-self" in args
    if not paths:
        paths = sorted(glob.glob(os.path.join(ROOT, "tests", "test_*.py")))
    if skip:
        paths = [p for p in paths if os.path.basename(p) != "test_selftest.py"]
    return paths


def _self_check() -> bool:
    """The runner asserts on itself: --skip-self expansion must hold while
    the plain (no-arg) expansion stays full. No suite needed."""
    noarg = _expand([])
    skipped = _expand(["--skip-self"])
    return (len(noarg) > 0 and len(skipped) == len(noarg) - 1
            and all(os.path.basename(p) != "test_selftest.py" for p in skipped))


def main(argv: list[str]) -> int:
    paths = _expand(argv[1:])
    passed = failed = 0
    failures: list[str] = []
    for path in paths:
        if not os.path.isabs(path):
            path = os.path.join(ROOT, path)
        name = os.path.basename(path)[:-3]
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            failed += 1
            failures.append(f"{name}:import (no loader)")
            continue
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
        except Exception as e:
            failed += 1
            failures.append(f"{name}:import {type(e).__name__}: {e}")
            continue
        for attr in sorted(dir(mod)):
            if not attr.startswith("test_"):
                continue
            try:
                getattr(mod, attr)()
                passed += 1
            except Exception as e:
                failed += 1
                failures.append(f"{name}:{attr} {type(e).__name__}: {e}")
    print(f"PASS={passed} FAIL={failed}")
    for f in failures:
        print(f"  FAIL {f}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
