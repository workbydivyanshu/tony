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


def todo_role(text: str) -> str:
    """Role dispatch from the architect's [role:X] tag (scripture Ch.4); untagged/unknown -> builder."""
    from . import tiers as tmod
    m = ROLE_TAG.search(text or "")
    if m and m.group(1) in tmod.ROLES:
        return m.group(1)
    return "builder"


def run_wave(b: dict, cwd: str = "/tmp") -> list:
    """Execute each wave item as a shell command. Flips boxes. Returns pass list."""
    from . import boulder as bmod
    results = []
    for i, item in enumerate(b["wave"]):
        cmd = F_LABEL.sub("", item["text"]).strip()
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


def _runslog_append(path: str, role: str, model: str, status: str, duration: float) -> None:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with _LOCK, open(path, "a") as f:
            f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} role={role} model={model} "
                    f"status={status} dur={duration:.1f}s\n")
    except OSError:
        pass


def role_call(role: str, model: str, subtask: str, workdir: str,
              runner=None, timeout: int = 600, runslog: str = RUNSLOG_DEFAULT,
              opencode_bin: str | None = None) -> dict:
    """One stateless role call. Returns {status, output, outfile, duration, model}."""
    from .catalog import resolve_bin
    os.makedirs(workdir, exist_ok=True)
    run = runner or subprocess.run
    t0 = time.time()
    try:
        proc = run([resolve_bin(opencode_bin), "run", "--model", model, subtask],
                   capture_output=True, text=True, timeout=timeout)
        ok = proc.returncode == 0
        output = (proc.stdout or "") + (proc.stderr or "")
    except Exception as e:  # runner exploded (timeout, missing binary)
        ok, output = False, f"role_call exception: {e}"
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
              runner=None, runslog: str = RUNSLOG_DEFAULT) -> None:
    """Execute a single TODO by index: role_call -> flip+log; demote once, else [BLOCKED]."""
    from . import boulder as bmod
    todo = b["todos"][i]
    role = todo.get("role") or todo_role(todo["text"])
    models = list(tier_models.get(role, []))
    if not models:
        todo["text"] += " [BLOCKED: no model in tier]"
        bmod.log(b, f"TODO {i+1} BLOCKED (no model)")
        return
    model = models[0]
    res = role_call(role, model, todo["text"], workdir, runner=runner,
                    runslog=runslog)
    if res["status"] == "ok":
        bmod.flip(b, i, True)
        bmod.log(b, f"TODO {i+1} done via {model} ({res['duration']:.0f}s) -> {res['outfile']}")
    else:
        bmod.log(b, f"TODO {i+1} fail via {model}: {(res['output'][:120])}")
        if len(models) > 1:
            model2 = models[1]
            res2 = role_call(role, model2, todo["text"], workdir, runner=runner,
                             runslog=runslog)
            if res2["status"] == "ok":
                bmod.flip(b, i, True)
                bmod.log(b, f"TODO {i+1} done on demote via {model2} -> {res2['outfile']}")
            else:
                todo["text"] += " [BLOCKED]"
                bmod.log(b, f"TODO {i+1} BLOCKED after demote")
        else:
            todo["text"] += " [BLOCKED]"
            bmod.log(b, f"TODO {i+1} BLOCKED (no fallback)")


def run_loop(b: dict, tier_models: dict, workdir: str,
             runner=None, runslog: str = RUNSLOG_DEFAULT,
             now_stamp: str | None = None, parallel: bool = False) -> dict:
    """Execute each unchecked TODO; demote+retry once. parallel=True runs
    consecutive [role:explorer] TODOs concurrently via threads (stdlib only);
    every other role stays sequential in index order."""
    import concurrent.futures as cf
    batch = []

    def flush():
        if not batch:
            return
        with cf.ThreadPoolExecutor(max_workers=len(batch)) as ex:
            list(ex.map(lambda j: _exec_one(b, j, tier_models, workdir, runner, runslog),
                        batch))
        batch.clear()

    for i, todo in enumerate(b["todos"]):
        if todo["box"]:
            continue
        if parallel and todo_role(todo["text"]) in PARALLEL_ROLES:
            batch.append(i)
        else:
            flush()
            _exec_one(b, i, tier_models, workdir, runner, runslog)
    flush()
    return b


def verify_wave(b: dict, max_verify: int = 3, cwd: str = "/tmp", fix_fn=None) -> list:
    """Wave retry loop (extracted from the CLI so --max-verify is testable).
    fix_fn(failed_texts) runs after each failed attempt; returns final pass list."""
    from . import boulder as bmod
    results: list = []
    for attempt in range(1, max(1, max_verify) + 1):
        results = run_wave(b, cwd=cwd)
        if all(results):
            break
        bmod.log(b, f"wave attempt {attempt} failed; feeding fix")
        if fix_fn is not None:
            fix_fn([w["text"] for w, ok in zip(b["wave"], results) if not ok])
    return results
