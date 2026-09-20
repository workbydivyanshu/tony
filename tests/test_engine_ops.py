"""V1 Task 3 RED proof: engine ops hardening — rate-limit backoff + log rotation.

Tests must FAIL against current engine.py (no rate-limit detection, no rotation).
All tests use fake runners + fake sleep_fn → milliseconds, zero real sleeping.
"""
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib import engine, boulder

TMP = "/tmp/tony-test-engine-ops"


def _clean():
    shutil.rmtree(TMP, ignore_errors=True)
    os.makedirs(TMP, exist_ok=True)


# ── Rate-limit backoff tests ────────────────────────────────────────────

def test_429_backoff_sequence():
    """role_call sees '429' in output → backoff [5] then returns fail.

    'max 2 attempts' = initial + 1 retry (P17: free-lane stalls cost the
    mission, not the role). Second failure triggers demote, NOT a second
    backoff sleep. This is the no-storm guarantee: backoff happens once per
    model, demote is the next step, never backoff-again."""
    _clean()
    sleep_calls = []
    call_n = [0]

    def fake_runner(cmd, **kw):
        call_n[0] += 1
        class R: pass
        r = R()
        r.returncode = 1
        r.stdout = ""
        r.stderr = "Error 429: too many requests"
        return r

    def fake_sleep(s):
        sleep_calls.append(s)

    runslog = os.path.join(TMP, "runs.log")
    res = engine.role_call("builder", "m1", "do X", workdir=TMP,
                           runner=fake_runner, runslog=runslog,
                           sleep_fn=fake_sleep)
    # 2 runner invocations: initial + 1 retry
    assert call_n[0] == 2, f"expected 2 attempts, got {call_n[0]}"
    # sleep called once with bounded backoff [5]
    assert sleep_calls == [5], f"expected [5], got {sleep_calls}"
    # Overall status is fail (backoff exhausted → demote path)
    assert res["status"] == "fail", f"expected fail, got {res['status']}"


def test_rate_limit_case_insensitive_signals():
    """All four signals — '429', 'rate limit', 'quota', 'overloaded' —
    detected case-insensitively."""
    _clean()
    signals = [
        "Rate Limit exceeded",
        "QUOTA reached",
        "Service Overloaded",
        "HTTP 429",
    ]
    for sig in signals:
        calls = []

        def fake_runner(cmd, _sig=sig, **kw):
            class R: pass
            r = R()
            r.returncode = 1
            r.stdout = ""
            r.stderr = _sig
            return r

        def fake_sleep(s):
            calls.append(s)

        runslog = os.path.join(TMP, "runs-sig.log")
        res = engine.role_call("builder", "m1", "do X", workdir=TMP,
                               runner=fake_runner, runslog=runslog,
                               sleep_fn=fake_sleep)
        assert calls == [5], f"signal '{sig}': expected [5], got {calls}"
        assert res["status"] == "fail", f"signal '{sig}': expected fail"


def test_no_rate_limit_no_backoff():
    """Non-rate-limit failures do NOT trigger backoff — immediate fail."""
    _clean()
    sleep_calls = []

    def fake_runner(cmd, **kw):
        class R: pass
        r = R()
        r.returncode = 1
        r.stdout = ""
        r.stderr = "segfault core dumped"
        return r

    def fake_sleep(s):
        sleep_calls.append(s)

    runslog = os.path.join(TMP, "runs-nosig.log")
    res = engine.role_call("builder", "m1", "do X", workdir=TMP,
                           runner=fake_runner, runslog=runslog,
                           sleep_fn=fake_sleep)
    assert sleep_calls == [], f"expected zero sleeps, got {sleep_calls}"
    assert res["status"] == "fail"


def test_rate_limit_success_on_retry():
    """429 on attempt 1, success on attempt 2 → OK, only [5] sleep."""
    _clean()
    sleep_calls = []
    call_n = [0]

    def fake_runner(cmd, **kw):
        call_n[0] += 1
        class R: pass
        r = R()
        if call_n[0] == 1:
            r.returncode = 1
            r.stdout = ""
            r.stderr = "429 busy"
        else:
            r.returncode = 0
            r.stdout = "SUCCESS"
            r.stderr = ""
        return r

    def fake_sleep(s):
        sleep_calls.append(s)

    runslog = os.path.join(TMP, "runs-retry-ok.log")
    res = engine.role_call("builder", "m1", "do X", workdir=TMP,
                           runner=fake_runner, runslog=runslog,
                           sleep_fn=fake_sleep)
    assert call_n[0] == 2, f"expected 2 attempts, got {call_n[0]}"
    assert sleep_calls == [5], f"expected [5], got {sleep_calls}"
    assert res["status"] == "ok", f"expected ok, got {res['status']}"


def test_backoff_then_demote_no_storm():
    """Integration: 2×429 on m1 → backoff [5] → fail → _exec_one demotes
    to m2 → m2 succeeds → overall ok.

    No-storm guarantee: sleep_calls has exactly [5] (backoff within m1),
    then m2 runs immediately (no extra sleep)."""
    _clean()
    sleep_calls = []
    call_n = [0]

    def fake_runner(cmd, **kw):
        call_n[0] += 1
        model = cmd[3] if len(cmd) > 3 else ""
        class R: pass
        r = R()
        if model == "m1":
            r.returncode = 1
            r.stdout = ""
            r.stderr = "429 rate limit"
        else:
            r.returncode = 0
            r.stdout = "OK demoted"
            r.stderr = ""
        return r

    def fake_sleep(s):
        sleep_calls.append(s)

    b = boulder.new("t")
    boulder.add_todo(b, "1. hard thing")
    engine._exec_one(b, 0, {"builder": ["m1", "m2"]}, workdir=TMP,
                     runner=fake_runner,
                     runslog=os.path.join(TMP, "runs-storm.log"),
                     sleep_fn=fake_sleep)
    # m1: 2 attempts + 1 sleep, m2: 1 attempt = 3 total runner calls
    assert call_n[0] == 3, f"expected 3 runner calls, got {call_n[0]}"
    # Sleeps only during m1 backoff, NOT after demote
    assert sleep_calls == [5], f"expected [5] (no storm), got {sleep_calls}"
    # Demote succeeded
    assert b["todos"][0]["box"] is True, f"expected box True"


def test_sleep_fn_default_is_none():
    """sleep_fn defaults to None (no backoff for legacy callers).
    When provided, backoff is active."""
    import inspect
    sig = inspect.signature(engine.role_call)
    assert "sleep_fn" in sig.parameters, "role_call must accept sleep_fn"
    default = sig.parameters["sleep_fn"].default
    assert default is None, f"default should be None, got {default}"


def test_no_sleep_fn_no_backoff():
    """Without sleep_fn, role_call does NOT retry on rate-limit — single call only."""
    _clean()
    calls = []

    def fake_runner(cmd, **kw):
        calls.append(1)
        class R: pass
        r = R()
        r.returncode = 1
        r.stdout = ""
        r.stderr = "429 rate limit"
        return r

    runslog = os.path.join(TMP, "runs-nosfn.log")
    res = engine.role_call("builder", "m1", "do X", workdir=TMP,
                           runner=fake_runner, runslog=runslog)
    assert len(calls) == 1, f"expected 1 runner call (no backoff), got {len(calls)}"
    assert res["status"] == "fail"


# ── Log rotation tests ──────────────────────────────────────────────────

def test_runslog_rotation_at_1mb():
    """When runs.log exceeds 1MB, rotate to runs.log.1 (single generation),
    then append continues in the fresh main file."""
    _clean()
    logpath = os.path.join(TMP, "runs.log")
    # Write 1.1MB (above threshold)
    big_line = "x" * 1100 + "\n"
    with open(logpath, "w") as f:
        for _ in range(1024):
            f.write(big_line)
    assert os.path.getsize(logpath) > 1_000_000, "precondition: >1MB"

    engine._runslog_append(logpath, "builder", "m1", "ok", 1.5)

    rot = logpath + ".1"
    assert os.path.exists(rot), f"rotation file {rot} must exist"
    assert os.path.getsize(rot) > 0, "rotation file must not be empty"
    assert os.path.getsize(logpath) < 2000, "main file must be small after rotation"
    with open(logpath) as f:
        assert "role=builder" in f.read(), "new append must be in fresh main file"


def test_runslog_no_rotation_below_1mb():
    """Sub-1MB logs append without rotation."""
    _clean()
    logpath = os.path.join(TMP, "runs-small.log")
    with open(logpath, "w") as f:
        f.write("small log\n")
    engine._runslog_append(logpath, "builder", "m1", "ok", 0.5)
    assert not os.path.exists(logpath + ".1"), "no rotation below 1MB"
    with open(logpath) as f:
        c = f.read()
    assert "small log" in c and "role=builder" in c


def test_timeout_default_unchanged():
    """timeout param still defaults to 600 — no signature break."""
    import inspect
    sig = inspect.signature(engine.role_call)
    assert sig.parameters["timeout"].default == 600
