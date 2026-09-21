"""critic_verdict.py — strict critic verdict parsing. Stdlib only.

The critic's own VERDICT line comes at the end of its message. But role_call
captures the WHOLE opencode session afterwards (transcript chrome, file reads)
— which can contain STALE "Verdict: ..." text from history (proven live
2026-09-18: P5a's 'Verdict: PASS' inside NOTEPAD.md leaked into a critic
transcript). Therefore parse() takes the FIRST explicit verdict hit, and
callers treat None as ISSUES — an unclear verdict is never a pass."""
import re

TRUNCATE_LEN = 80

_LINE = re.compile(r"verdict\s*:\s*([^\n]+)", re.I)


def child_render(content: str, max_len: int = TRUNCATE_LEN) -> str:
    """Render child evidence lines with truncation.

    Prefixes with CHILD and truncates to max_len characters."""
    prefix = "CHILD: "
    truncated = content[: max_len - len(prefix)]
    return prefix + truncated


def parse(output: str) -> str | None:
    hits = _LINE.findall(output or "")
    if not hits:
        return None
    val = hits[0].strip()
    head = val.split(":", 1)[0].strip()
    if head.lower() in ("issues", "issue"):
        return "ISSUES"
    return val


def is_issues(output: str) -> bool:
    v = parse(output)
    if v is None:
        return True  # missing verdict = not proven passed
    return v.lower().startswith("issue")
