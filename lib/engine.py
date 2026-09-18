"""engine.py — the agent loop. Stdlib only.

role_call = subprocess `opencode run --model <model> <subtask>`.
NEVER raw HTTP to gateways (scripture Ch.0 architectural law).
run_loop: per unchecked TODO -> role call -> flip+log; on failure demote
once within tier, retry, else [BLOCKED]. Every call appends runs.log.
"""
import os
import subprocess
import time

RUNSLOG_DEFAULT = os.path.join(os.path.expanduser("~"), ".tony", "runs.log")


def _runslog_append(path: str, role: str, model: str, status: str, duration: float) -> None:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a") as f:
            f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} role={role} model={model} "
                    f"status={status} dur={duration:.1f}s\n")
    except OSError:
        pass


def role_call(role: str, model: str, subtask: str, workdir: str,
              runner=None, timeout: int = 600) -> dict:
    """One stateless role call. Returns {status, output, outfile, duration, model}."""
    os.makedirs(workdir, exist_ok=True)
    run = runner or subprocess.run
    t0 = time.time()
    try:
        proc = run(["opencode", "run", "--model", model, subtask],
                   capture_output=True, text=True, timeout=timeout)
        ok = proc.returncode == 0
        output = (proc.stdout or "") + (proc.stderr or "")
    except Exception as e:  # runner exploded (timeout, missing binary)
        ok, output = False, f"role_call exception: {e}"
    dur = time.time() - t0
    n = len([f for f in os.listdir(workdir) if f.endswith(".md")]) + 1
    outfile = os.path.join(workdir, f"{n:02d}-{role}.md")
    try:
        with open(outfile, "w") as f:
            f.write(f"# {role} ({model}) — {time.strftime('%Y-%m-%d %H:%M')}\n\n{output}\n")
    except OSError:
        pass
    return {"status": "ok" if ok else "fail", "output": output,
            "outfile": outfile, "duration": dur, "model": model}


def run_loop(b: dict, tier_models: dict, workdir: str,
             runner=None, runslog: str = RUNSLOG_DEFAULT,
             now_stamp: str | None = None) -> dict:
    """Execute each unchecked TODO with tier_models[role][0]; demote+retry once."""
    from . import boulder as bmod
    stamps = []
    for i, todo in enumerate(b["todos"]):
        if todo["box"]:
            continue
        role = todo.get("role", "builder")
        models = list(tier_models.get(role, []))
        if not models:
            todo["text"] += " [BLOCKED: no model in tier]"
            bmod.log(b, f"TODO {i+1} BLOCKED (no model)")
            continue
        model = models[0]
        res = role_call(role, model, todo["text"], workdir, runner=runner)
        _runslog_append(runslog, role, model, res["status"], res["duration"])
        if res["status"] == "ok":
            bmod.flip(b, i, True)
            bmod.log(b, f"TODO {i+1} done via {model} ({res['duration']:.0f}s) -> {res['outfile']}")
        else:
            bmod.log(b, f"TODO {i+1} fail via {model}: {(res['output'][:120])}")
            if len(models) > 1:
                model2 = models[1]
                res2 = role_call(role, model2, todo["text"], workdir, runner=runner)
                _runslog_append(runslog, role, model2, res2["status"], res2["duration"])
                if res2["status"] == "ok":
                    bmod.flip(b, i, True)
                    bmod.log(b, f"TODO {i+1} done on demote via {model2} -> {res2['outfile']}")
                else:
                    todo["text"] += " [BLOCKED]"
                    bmod.log(b, f"TODO {i+1} BLOCKED after demote")
            else:
                todo["text"] += " [BLOCKED]"
                bmod.log(b, f"TODO {i+1} BLOCKED (no fallback)")
    return b
