"""waveguard.py — P19a trust boundary for model-authored shell commands.

Wave items and research verification commands are authored by models. They run
with shell=True by design (pipes/globs are the point), so every command passes
through check() BEFORE execution:

1. Deny-list: destructive/system patterns never execute (sudo, disk writers,
   fork bombs, shutdown, piped remote shells, chmod/chown sweeps...).
2. sh -n syntax parse: commands that cannot parse never execute.

Failure doctrine: a blocked command FAILS its wave item with a logged reason
and is never passed to subprocess. This is a deny-list, not a sandbox — the
real boundary remains "Tony runs only missions you authored" (same trust the
role prompts already have). What P19a removes is the UNREVIEWED-EXECUTION
footgun where a hallucinated or injected wave command could destroy state.
"""
import re as _re
import subprocess as _sp

# (label, regex) — matched case-insensitively against the command text.
_DENY = (
    ("privilege escalation (sudo/su)", r"\b(?:sudo|su)\b"),
    ("power/state control", r"\b(?:shutdown|reboot|poweroff|halt)\b|\binit\s+0\b"),
    ("filesystem format", r"\bmkfs(?:\.\w+)?\b"),
    ("raw disk write", r"\bdd\b[^|;&]*\bof=/dev/|\bwrite\b.*\bof=/dev/"),
    ("fork bomb", r":\s*\(\s*\)\s*\{"),
    ("piped remote shell", r"\b(?:curl|wget)\b[^|;&]*\|\s*(?:sudo\s+)?(?:ba|z|da)?sh\b"),
    ("remote script exec", r"\b(?:curl|wget)\b[^|;&]*\|\s*(?:sudo\s+)?(?:ba|z|da)?sh\b"),
    ("recursive permission sweep on root", r"\bchmod\b[^|;&]*-R[^|;&]*\s/(?:\s|$)"),
    ("recursive ownership sweep on root", r"\bchown\b[^|;&]*-R[^|;&]*\s/(?:\s|$)"),
    ("root rm", r"\brm\b[^|;&]*-[a-zA-Z]*[rf][a-zA-Z]*[^|;&]*\s(?:/|~|\*)(?:\s|$)"),
    ("device node write", r">\s*/dev/(?:sd|nvme|hd|vd|disk)"),
    ("initramfs/kernel image tamper", r"\b(?:dd|cp)\b[^|;&]*\b(?:/boot/|/lib/modules/)"),
    ("passwd/shadow write", r">\s*/etc/(?:passwd|shadow|sudoers)"),
)

_COMPILE = [(label, _re.compile(pattern, _re.IGNORECASE)) for label, pattern in _DENY]


def _syntax_ok(cmd: str) -> tuple[bool, str]:
    """sh -n parse: syntax errors never execute."""
    try:
        r = _sp.run(["sh", "-n", "-c", cmd], capture_output=True, text=True, timeout=10)
    except Exception as e:
        return False, f"syntax check failed: {type(e).__name__}"
    if r.returncode != 0:
        return False, "shell syntax error (sh -n): " + (r.stderr or "").strip()[:200]
    return True, ""


def check(cmd: str) -> tuple[bool, str]:
    """Return (safe, reason). safe=False means NEVER execute."""
    cmd = (cmd or "").strip()
    if not cmd:
        return False, "empty command"
    for label, rx in _COMPILE:
        m = rx.search(cmd)
        if m:
            return False, f"blocked: {label} (match: {m.group(0)[:60]!r})"
    ok, reason = _syntax_ok(cmd)
    return ok, reason
