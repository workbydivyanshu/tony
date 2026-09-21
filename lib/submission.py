"""submission.py — submission pipeline contracts. Stdlib only."""
import re


def tag_parse(text: str) -> str | None:
    """Parse [mission:slug] -> slug; missing/bad tag -> None."""
    m = re.match(r"^\[mission:(.+)\]$", text.strip())
    if m and m.group(1).strip():
        return m.group(1).strip()
    return None


def child_budget(parent_timeout: int) -> int:
    """child_budget(600) -> 300; child_budget(90) -> 60 floor."""
    return max(60, parent_timeout // 2)


def execute(home: str, depth: int, mission_fn) -> str:
    """depth-2 tag -> BLOCKED; mission_fn must not be called."""
    if depth >= 2:
        return "BLOCKED"
    mission_fn()
    return "OK"


def spawn_children(home: str, tags: list) -> str:
    """4th child tag -> BLOCKED; max-children is 3."""
    if len(tags) > 3:
        return "BLOCKED"
    return "OK"


def parent_flip(score: int, wave: str) -> str:
    """72+ green -> done; 59 -> BLOCKED; red-wave -> BLOCKED."""
    if score >= 60 and wave == "green":
        return "done"
    return "BLOCKED"


def summarize(home: str, text: str) -> str:
    """summary must be <=3 lines and <=160 chars."""
    lines = text.splitlines()
    truncated = "\n".join(lines[:3])
    if len(truncated) > 160:
        truncated = truncated[:160]
    return truncated


def _is_hostile(cmd: str) -> bool:
    """Check if a command is destructive/hostile (stdlib-only deny-list)."""
    c = cmd.strip().lower()
    # Recursive rm on any target
    if re.search(r"\brm\b.*\s-[a-zA-Z]*[rR]", c):
        return True
    # rm -rf / or similar root targets
    if re.search(r"\brm\b.*\s-[a-zA-Z]*[rf][a-zA-Z]*.*\s(?:/|~|\*)", c):
        return True
    # sudo/su privilege escalation
    if re.search(r"\b(?:sudo|su)\b", c):
        return True
    # Power/state control
    if re.search(r"\b(?:shutdown|reboot|poweroff|halt)\b", c):
        return True
    # Fork bomb
    if re.search(r":\s*\(\s*\)\s*\{", c):
        return True
    # Piped remote shell
    if re.search(r"\b(?:curl|wget)\b.*\|\s*(?:sudo\s+)?(?:(?:ba|z|da)?sh|python[23]?|perl|ruby|php|node)\b", c):
        return True
    # Root rm with -r or -rf
    if re.search(r"\brm\b.*\s-[a-zA-Z]*r", c) and re.search(r"\s(?:/|~|\*)", c):
        return True
    return False


def run_wave(home: str, cmd: str, exec_fn) -> str:
    """Hostile child wave -> BLOCKED; wave commands never executed."""
    if _is_hostile(cmd):
        return "BLOCKED"
    exec_fn(cmd)
    return "OK"


def architect_prompt() -> str:
    """Architect prompt must include tag documentation."""
    return (
        "Mission tags:\n"
        "  [mission:slug] — tag a boulder item with a mission slug.\n"
        "  child_budget(parent_timeout) — returns half the parent timeout "
        "with a 60s floor.\n"
        "  BLOCKED — returned when a guard condition fails (depth>=2, "
        ">3 tags, hostile command, score<60 or red wave).\n"
        "All mission items must carry a [mission:] tag. "
        "Use child_budget() to size child timeouts. "
        "Violations return BLOCKED."
    )
