"""callshape.py — latency honesty tools. Stdlib only.

P16 premise (Vianca, verified): `opencode run` in the TUI answers in seconds
on the same free models that take Tony minutes. Something in the CALL SHAPE
differs: cold session per call, agent-harness multi-round overhead, prompt
shape, or retry/backoff. This module measures rather than guesses:
timed_run() wall-clocks any argv; count_internal_steps() counts the Sisyphus
transcript markers ('→' tool echoes) in a role output so a '1 call' that was
secretly N model round-trips shows up as N."""
import re
import subprocess
import time

STEP_MARK = re.compile(r"^→\s", re.M)


def timed_run(argv: list, **kw) -> tuple:
    """Run argv, return (argv, wall_seconds)."""
    t0 = time.time()
    subprocess.run(argv, capture_output=True, **kw)
    return argv, time.time() - t0


def count_internal_steps(role_output: str) -> int:
    """Count '→ <tool>' transcript echoes = internal agent round-trips."""
    return len(STEP_MARK.findall(role_output or ""))
