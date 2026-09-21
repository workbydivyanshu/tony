"""Mission tag parsing and child-spawn primitives for Tony."""
import re

MISSION_TAG = re.compile(r"^[a-z][a-z0-9-]*$")
MAX_DEPTH = 2
MAX_CHILDREN = 2
DONE_THRESHOLD = 60


def parse_mission_tag(tag: str) -> str | None:
    if not tag or not MISSION_TAG.match(tag):
        return None
    return tag


def resolve_tag(text: str):
    """Dispatch precedence: mission tag beats role tag beats default.

    Returns (kind, name): ("mission", slug), ("role", name), or
    ("role", "builder") for untagged TODOs (existing convention).
    """
    m = re.search(r"\[mission:([A-Za-z0-9][A-Za-z0-9_-]*)\]", text or "")
    if m:
        return ("mission", m.group(1))
    r = re.search(r"\[role:([A-Za-z0-9_-]+)\]", text or "")
    if r:
        return ("role", r.group(1))
    return ("role", "builder")


def child_slug(parent_tag: str, child_name: str) -> str:
    return f"{parent_tag}/{child_name}"


def child_timeout(parent_timeout: int) -> int:
    return max(parent_timeout // 2, 60)


def spawn_child(depth: int) -> None:
    if depth > MAX_DEPTH:
        raise ValueError(f"depth {depth} exceeds MAX_DEPTH {MAX_DEPTH}")
