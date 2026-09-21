"""engine.py — the agent loop. Stdlib only.

role_call = subprocess `opencode run --model <model> <subtask>`.
NEVER raw HTTP to gateways (scripture Ch.0 architectural law).
run_loop: per unchecked TODO -> role call -> flip+log; on failure demote
once within tier, retry, else [BLOCKED]. Every call appends runs.log.
"""
import os
import re
import subprocess
import threading
import time

_LOCK = threading.Lock()

ANSI = re.compile(r"\x1b\[[0-9;]*m")


def sanitize(raw: str) -> str:
    """Parse boundary: strip ANSI + drop pre-boulder transcript chrome (ISSUE-4)."""
    text = ANSI.sub("", raw)
    i = text.find("# Boulder")
    return text[i:] if i >= 0 else text


F_LABEL = re.compile(r"^F\d+\.\s*")
ROLE_TAG = re.compile(r"\[role:(\w+)\]")
PARALLEL_ROLES = ("explorer",)
BLOCKED_TAG = "[BLOCKED]"


def has_blocked(b: dict) -> bool:
    """True when any TODO carries a [BLOCKED] marker (demote-exhausted or contained exception)."""
    return any(BLOCKED_TAG in (t.get("text") or "") for t in b.get("todos", []))


def should_run_wave(b: dict, keep_going: bool = False) -> bool:
    """Wave gate for --keep-going: clean boulders always run the wave;
    BLOCKED boulders run it only with keep_going=True, otherwise the wave
    is skipped and the report scores the TODOs alone."""
    if not has_blocked(b):
        return True
    return bool(keep_going)


def todo_role(text: str) -> str:
    """Role dispatch from the architect's [role:X] tag (scripture Ch.4); untagged/unknown -> builder."""
    from . import tiers as tmod
    m = ROLE_TAG.search(text or "")
    if m and m.group(1) in tmod.ROLES:
        return m.group(1)
    return "builder"


def resolve_role(todo: dict, b: dict | None = None) -> str:
    """Single precedence for role dispatch (review note 1): explicit todo["role"]
    wins when valid; else the architect's [role:X] tag; else builder.
    Unknown tags fall back to builder WITH a boulder log line when b is given
    (review note 2) so architect typos are visible instead of silent.
    Callers scanning without a boulder (run_loop batching) pass b=None to stay pure;
    _exec_one passes b so the fallback is recorded exactly once."""
    from . import boulder as bmod
    from . import tiers as tmod
    explicit = (todo or {}).get("role")
    if explicit in tmod.ROLES:
        return explicit
    m = ROLE_TAG.search((todo or {}).get("text") or "")
    if m:
        if m.group(1) in tmod.ROLES:
            return m.group(1)
        if b is not None:
            bmod.log(b, f"unknown [role:{m.group(1)}] -> builder "
                        f"(typo? valid: {sorted(tmod.ROLES)})")
        return "builder"
    return "builder"


def run_wave(b: dict, cwd: str = "/tmp") -> list:
    """Execute each wave item as a shell command. Flips boxes. Returns pass list.

    TRUST BOUNDARY (review note 7): wave commands come from the architect, which
    tony already trusts with TODO text executed via role prompts — same trust.
    shell=True is intentional for architect ergonomics (pipes, &&, grep -q).
    Never feed untrusted third-party text here; waves auto-retry with builder
    fixes, so a malicious command would re-run up to max_verify times."""
    from . import boulder as bmod
    from . import waveguard
    results = []
    for i, item in enumerate(b["wave"]):
        cmd = F_LABEL.sub("", item["text"]).strip()
        safe, reason = waveguard.check(cmd)
        if not safe:
            # P19a: never hand a deny-listed/unparseable command to the shell.
            bmod.flip(b, i, False, section="wave")
            bmod.log(b, f"wave {i+1} BLOCKED by waveguard: {reason}")
            results.append(False)
            continue
        try:
            proc = subprocess.run(cmd, shell=True, capture_output=True,
                                  text=True, timeout=300, cwd=cwd)
            passed = proc.returncode == 0
        except Exception:
            passed, proc = False, None
        bmod.flip(b, i, passed, section="wave")
        out = (proc.stdout or "") + (proc.stderr or "") if proc else "exception"
        bmod.log(b, f"wave {i+1} {'PASS' if passed else 'FAIL'}: {item['text'][:100]}")
        bmod.log(b, f"wave {i+1} output: {out.strip()[:300]}")
        results.append(passed)
    return results

RUNSLOG_DEFAULT = os.path.join(os.path.expanduser("~"), ".tony", "runs.log")
RUNSLOG_MAX_BYTES = 1_000_000

RATE_LIMIT_SIGNS = ("429", "rate limit", "quota", "overloaded")
BACKOFF_SECS = (5, 10)
MAX_BACKOFF_ATTEMPTS = 2

# Per-role wall-clock budgets (P17: free-lane stalls cost the mission, not the
# role). Values are fractions of the mission timeout: architect needs the full
# plan window, builders get most of it, cheap roles get capped hard.
ROLE_TIMEOUT_FRAC = {
    "architect": 1.0,
    "builder": 0.8,
    "researcher": 0.6,
    "critic": 0.6,
    "explorer": 0.4,
    "scribe": 0.2,
}


def role_timeout(role: str, mission_timeout: int) -> int:
    """Wall-clock budget for one role call. Unknown roles get the full window."""
    return int(mission_timeout * ROLE_TIMEOUT_FRAC.get(role, 1.0))


def effective_timeout(base: int, fast: bool = False) -> int:
    """Mission timeout after --fast. Halves the window, floor 60s so cheap
    roles keep a usable budget (scribe 0.2 * 60 = 12s minimum)."""
    if not fast:
        return base
    return max(60, base // 2)


def _looks_rate_limited(output: str) -> bool:
    low = (output or "").lower()
    return any(s in low for s in RATE_LIMIT_SIGNS)


def _runslog_append(path: str, role: str, model: str, status: str, duration: float) -> None:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with _LOCK:
            try:
                if os.path.getsize(path) > RUNSLOG_MAX_BYTES:
                    try:
                        if os.path.exists(path + ".1"):
                            os.remove(path + ".1")
                    except OSError:
                        pass
                    os.rename(path, path + ".1")
            except OSError:
                pass
            with open(path, "a") as f:
                f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} role={role} model={model} "
                        f"status={status} dur={duration:.1f}s\n")
    except OSError:
        pass


def role_call(role: str, model: str, subtask: str, workdir: str,
              runner=None, timeout: int = 600, runslog: str = RUNSLOG_DEFAULT,
              opencode_bin: str | None = None, sleep_fn=None) -> dict:
    """One stateless role call. Returns {status, output, outfile, duration, model}.

    sleep_fn=None (default) preserves legacy single-attempt behavior exactly.
    With sleep_fn, rate-limit signals trigger bounded same-model retries:
    initial + 1 retry max, sleep [5]; the second failure returns fail
    WITHOUT a second sleep so the caller demotes next. Retries never cross
    models, so backoff and demote-once-then-BLOCKED compose with no storms.
    Sleeps run outside _LOCK so parallel explorers never block each other."""
    from .catalog import resolve_bin
    os.makedirs(workdir, exist_ok=True)
    run = runner or subprocess.run
    t0 = time.time()
    output, ok = "", False
    max_tries = MAX_BACKOFF_ATTEMPTS if sleep_fn is not None else 1
    for attempt in range(max_tries):
        try:
            proc = run([resolve_bin(opencode_bin), "run", "--model", model, subtask],
                       capture_output=True, text=True, timeout=timeout,
                       cwd=workdir)
            ok = proc.returncode == 0
            output = (proc.stdout or "") + (proc.stderr or "")
        except Exception as e:  # runner exploded (timeout, missing binary)
            ok, output = False, f"role_call exception: {e}"
        if ok or sleep_fn is None or not _looks_rate_limited(output):
            break
        if attempt < max_tries - 1:
            sleep_fn(BACKOFF_SECS[min(attempt, len(BACKOFF_SECS) - 1)])
    dur = time.time() - t0
    _runslog_append(runslog, role, model, "ok" if ok else "fail", dur)
    with _LOCK:  # outfile numbering must be unique under threaded parallel explorers
        n = len([f for f in os.listdir(workdir) if f.endswith(".md")]) + 1
        outfile = os.path.join(workdir, f"{n:02d}-{role}.md")
        try:
            with open(outfile, "w") as f:
                f.write(f"# {role} ({model}) — {time.strftime('%Y-%m-%d %H:%M')}\n\n{output}\n")
        except OSError:
            pass
    return {"status": "ok" if ok else "fail", "output": output,
            "outfile": outfile, "duration": dur, "model": model}


def _exec_one(b: dict, i: int, tier_models: dict, workdir: str,
              runner=None, runslog: str = RUNSLOG_DEFAULT,
              sleep_fn=None, timeout: int = 600) -> None:
    """Execute a single TODO by index: role_call -> flip+log; demote once, else [BLOCKED].

    Exception guard (review note 5): a filesystem blowup (workdir removed mid-run,
    listdir raising inside the lock) marks THIS TODO [BLOCKED] instead of aborting
    the mission via flush() — sequential and parallel modes share the guarantee."""
    from . import boulder as bmod
    try:
        todo = b["todos"][i]
        role = resolve_role(todo, b)
        models = list(tier_models.get(role, []))
        if not models:
            todo["text"] += " [BLOCKED: no model in tier]"
            bmod.log(b, f"TODO {i+1} BLOCKED (no model)")
            return
        model = models[0]
        res = role_call(role, model, todo["text"], workdir, runner=runner,
                        timeout=role_timeout(role, timeout), runslog=runslog, sleep_fn=sleep_fn)
    except Exception as e:  # makedirs/listdir/etc blew up — contain it
        try:
            b["todos"][i]["text"] += " [BLOCKED]"
        except Exception:
            pass
        bmod.log(b, f"TODO {i+1} BLOCKED (exception: {type(e).__name__}: {str(e)[:120]})")
        return
    if res["status"] == "ok":
        bmod.flip(b, i, True)
        bmod.log(b, f"TODO {i+1} done via {model} ({res['duration']:.0f}s) -> {res['outfile']}")
    else:
        bmod.log(b, f"TODO {i+1} fail via {model}: {(res['output'][:120])}")
        if len(models) > 1:
            model2 = models[1]
            res2 = role_call(role, model2, todo["text"], workdir, runner=runner,
                             timeout=role_timeout(role, timeout), runslog=runslog, sleep_fn=sleep_fn)
            if res2["status"] == "ok":
                bmod.flip(b, i, True)
                bmod.log(b, f"TODO {i+1} done on demote via {model2} -> {res2['outfile']}")
            else:
                todo["text"] += " [BLOCKED]"
                bmod.log(b, f"TODO {i+1} BLOCKED after demote")
        else:
            todo["text"] += " [BLOCKED]"
            bmod.log(b, f"TODO {i+1} BLOCKED (no fallback)")


_MISSION_FN_SENTINEL = object()


def run_loop(b: dict, tier_models: dict, workdir: str,
             runner=None, runslog: str = RUNSLOG_DEFAULT,
             parallel: bool = False, sleep_fn=None, timeout: int = 600,
             mission_fn=_MISSION_FN_SENTINEL) -> dict:
    """Execute each unchecked TODO; demote+retry once. parallel=True runs
    consecutive [role:explorer] TODOs concurrently via threads (stdlib only);
    every other role stays sequential in index order.
    Batch scan uses resolve_role(todo) pure (no log); _exec_one re-resolves with
    b and records the unknown-tag fallback exactly once (review note 1).
    When mission_fn is provided, it is called as mission_fn(text, slug)
    for each unchecked TODO instead of role_call; mission_fn=None marks
    the TODO as BLOCKED."""
    import concurrent.futures as cf
    import re as _re
    batch: list = []

    def _mission_slug(text: str) -> str:
        m = _re.search(r"\[mission:([A-Za-z0-9][A-Za-z0-9_-]*)\]", text or "")
        return m.group(1) if m else ""

    def flush():
        if not batch:
            return
        with cf.ThreadPoolExecutor(max_workers=len(batch)) as ex:
            list(ex.map(lambda j: _exec_one(b, j, tier_models, workdir, runner, runslog,
                                        sleep_fn, timeout),
                            batch))
        batch.clear()

    for i, todo in enumerate(b["todos"]):
        if todo["box"]:
            continue
        if mission_fn is not _MISSION_FN_SENTINEL:
            from . import boulder as bmod
            from lib import fold as _fold
            if mission_fn is None:
                todo["text"] += " [BLOCKED]"
                bmod.log(b, "mission dispatch disabled (mission_fn=None)")
            else:
                slug = _mission_slug(todo["text"])
                try:
                    result = mission_fn(todo["text"], slug)
                except Exception as e:
                    todo["text"] += f" [BLOCKED: mission {slug} raised {type(e).__name__}]"
                    bmod.log(b, f"mission {slug}: exception {e}")
                    continue
                score = result[0] if isinstance(result, tuple) else 0
                wave_ok = result[1] is True if isinstance(result, tuple) else False
                if wave_ok and score >= _fold.DONE_THRESHOLD:
                    todo["box"] = True
                    bmod.log(b, f"mission {slug}: score {score}, evidence folded")
                else:
                    todo["text"] += f" [BLOCKED: mission {slug} scored {score}]"
                    bmod.log(b, f"mission {slug}: score {score}, held")
            continue
        if parallel and resolve_role(todo) in PARALLEL_ROLES:
            batch.append(i)
        else:
            flush()
            _exec_one(b, i, tier_models, workdir, runner, runslog, sleep_fn, timeout)
    flush()
    return b


def verify_wave(b: dict, max_verify: int = 3, cwd: str = "/tmp", fix_fn=None) -> list:
    """Wave retry loop (extracted from the CLI so --max-verify is testable).
    max_verify = TOTAL attempts (min 1 — --max-verify 0 still verifies once).
    fix_fn(failed_texts) runs between attempts only, never after the final one
    (review note 3: the old code burned a fix whose output was never re-run).
    Re-runs execute every wave item fresh, so a prior PASS can un-flip on a
    later attempt; final results reflect the last run (review note 4)."""
    from . import boulder as bmod
    total = max(1, max_verify)
    results: list = []
    for attempt in range(1, total + 1):
        results = run_wave(b, cwd=cwd)
        if all(results):
            break
        if attempt < total:
            if fix_fn is not None:
                bmod.log(b, f"wave attempt {attempt} failed; feeding fix")
                fix_fn([w["text"] for w, ok in zip(b["wave"], results) if not ok])
            else:
                bmod.log(b, f"wave attempt {attempt} failed; no fix_fn, re-running")
        else:
            bmod.log(b, f"wave attempt {attempt} failed; wave exhausted ({total} attempts)")
    return results


def critic_gate(output) -> str:
    """Critic gate: return "PASS" iff case-insensitive word-boundary PASS
    (regex r"\bPASS\b", re.IGNORECASE) is present in output; else "ISSUES".
    None/empty input -> "ISSUES". "BYPASS"/"PASSED" must NOT match."""
    if not output:
        return "ISSUES"
    if re.search(r"\bPASS\b", output, re.IGNORECASE):
        return "PASS"
    return "ISSUES"


def critic_gate_detail(output) -> tuple:
    """Strict critic gate: parse 'VERDICT: PASS' or 'VERDICT: ISSUES' line.

    Returns (gate, strong) where:
      gate = "PASS" or "ISSUES"
      strong = True if strict VERDICT line matched (case-insensitive),
               False if legacy word-boundary fallback was used.

    None/empty -> ("ISSUES", False).  "BYPASS"/"PASSED" do not match word-boundary PASS."""
    if not output:
        return ("ISSUES", False)
    # Strict: require VERDICT: PASS or VERDICT: ISSUES on its own line
    m = re.search(r"^\s*VERDICT:\s*(PASS|ISSUES)\s*$", output,
                  re.IGNORECASE | re.MULTILINE)
    if m:
        gate = m.group(1).upper()
        return (gate, True)
    # Legacy fallback: word-boundary PASS
    if re.search(r"\bPASS\b", output, re.IGNORECASE):
        return ("PASS", False)
    return ("ISSUES", False)


def evidence_coverage(output: str, todos: list) -> float:
    """Fraction of TODO indices referenced in output (0.0–1.0).

    Matches 'TODO N', '#N', and line-leading 'N.' (1-based).
    Empty todos -> 1.0."""
    if not todos:
        return 1.0
    n = len(todos)
    if not output:
        return 0.0
    indices = set()
    # Match TODO N (case-insensitive)
    for m in re.finditer(r"\b[Tt][Oo][Dd][Oo]\s+(\d+)", output):
        indices.add(int(m.group(1)))
    # Match #N
    for m in re.finditer(r"#(\d+)", output):
        indices.add(int(m.group(1)))
    # P19b: line-leading numbered evidence only — the old any-position regex
    # matched version strings ("Python 3. 14") as TODO coverage.
    for m in re.finditer(r"(?m)^\s*(\d+)\.\s", output):
        indices.add(int(m.group(1)))
    covered = sum(1 for i in range(1, n + 1) if i in indices)
    return covered / n


def apply_critic_gate(b: dict, gate: str, keep_going: bool = False,
                      fix_fn=None, critic_output: str = "") -> tuple:
    """Critic-gate decision after a critic call. Returns (gate, fix_status).

    P22: fix_status is "none" (PASS / no fix needed), "ok" (fix_fn ran and
    reported success), "fail" (fix_fn ran and reported failure/raised), or
    "held" (ISSUES with fix needed but no fix ran: fix_fn=None, or
    --keep-going bypass where the human owns the override).

    P19 ISSUES semantics preserved: hold logged + one bounded fix_fn call;
    ISSUES + keep_going -> override logged, no fix.
    """
    from . import boulder as bmod
    bmod.log(b, f"critic gate: {gate}")
    if gate != "ISSUES":
        return (gate, "none")
    if keep_going:
        bmod.log(b, "critic gate: ISSUES hold overridden by --keep-going")
        return (gate, "held")
    bmod.log(b, "critic gate: ISSUES; holding wave for builder fix")
    if fix_fn is None:
        bmod.log(b, "critic gate: ISSUES; NO FIX available — wave OVERRIDE if run")
        return (gate, "held")
    try:
        result = fix_fn([critic_output])
        ok = (result != "fail") and result is not False
    except Exception as e:
        bmod.log(b, f"critic gate: builder fix FAILED ({type(e).__name__})")
        ok = False
    if ok:
        bmod.log(b, "critic gate: builder fix ok")
    else:
        # P22: the wave may still run under --yes/headless, but the boulder
        # must say so EXPLICITLY before any wave line lands.
        bmod.log(b, "critic gate: ISSUES OVERRIDE — builder fix failed; "
                    "wave results are UNVERIFIED-until-they-pass")
    return (gate, "ok" if ok else "fail")
