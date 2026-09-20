"""packs.py — domain pack loader (P18). Stdlib only.

A pack is a small markdown doctrine file at ~/.tony/packs/<name>.md.
Missions may reference packs inline with `@pack:<name>`; expansion replaces
each reference with the pack text (capped at 8KB) so scheduled/default jobs
stay short in schedule.json while their real payload stays editable on disk.

Failure doctrine: a missing/unreadable pack is EMPTY, never an exception —
a bad pack must not kill a scheduled mission; it degrades to the mission text.

P18 Hermes-gap defaults: morning-briefing (07:00 daily) and memory-hygiene
(Sun 09:00). ensure_defaults() is idempotent: missing pack files are seeded,
missing schedule jobs are added, existing files/jobs are never overwritten.
"""
import os as _os
import re as _re

PACK_CAP = 8192
_PACK_RE = _re.compile(r"@pack:([A-Za-z0-9][A-Za-z0-9_-]*)")
_NAME_RE = _re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*")


def packs_dir(home: str | None = None) -> str:
    return _os.path.join(home or _os.path.expanduser("~"), ".tony", "packs")


def _pack_path(name: str, home: str | None) -> str:
    # slug-only names: traversal (../, absolute paths, hidden files) never reads
    if not name or not _NAME_RE.fullmatch(name):
        return ""
    return _os.path.join(packs_dir(home), name + ".md")


def read_pack(name: str, home: str | None = None) -> str:
    """Pack text, whitespace-trimmed and capped. Missing/unreadable -> ''. """
    p = _pack_path(name, home)
    if not p:
        return ""
    try:
        if _os.path.isdir(p):
            return ""
        with open(p) as f:
            return f.read(PACK_CAP).strip()
    except OSError:
        return ""


def list_packs(home: str | None = None) -> list[str]:
    try:
        names = sorted(_os.listdir(packs_dir(home)))
    except OSError:
        return []
    return [n[:-3] for n in names if n.endswith(".md")]


def expand(text: str, home: str | None = None) -> str:
    """Replace every `@pack:<name>` with the pack body (missing -> '')."""
    return _PACK_RE.sub(lambda m: read_pack(m.group(1), home), text or "")


def has_pack_ref(text: str) -> bool:
    return bool(_PACK_RE.search(text or ""))


MORNING_BRIEFING_PACK = """\
# Morning Briefing (P18 default)

Produce a TEXT-ONLY morning briefing. 3-5 bullets maximum, no filler, no preamble.

Order:
1. Date/day and one line of what today is for.
2. Highest-priority commitment or deadline visible in reachable context.
3. Anything blocked or stale since yesterday (workspaces, trackers, memory).
4. One concrete next action for the day — not a list of five.

Rules:
- Never invent calendar/mail/commit facts. If a source is unreachable, write
  `unavailable` for that bullet and move on.
- No voice, no TTS framing. This is text only.
- End with exactly: BRIEF COMPLETE
"""

MEMORY_HYGIENE_PACK = """\
# Memory Hygiene (P18 default, weekly)

Review the durable memory files that exist in this environment:
- ~/.fleet/memory/MEMORY.md (fleet timeline, newest first)
- ~/.tony/memory/*.md (Tony's own recall store)

Do:
1. Read them (read-only first; no rewrites yet).
2. Identify: duplicates, stale dated facts superseded by newer entries,
   and entries that contradict each other.
3. Report a SHORT hygiene list: KEEP / CONSOLIDATE / DROP, one line each,
   with the exact line text (or a unique prefix) so a human/delegate can act.

Rules:
- Never rewrite entries you did not write unless the mission explicitly says so.
- Never drop preferences or medical/legal/financial facts.
- If nothing is stale, say so in one line — silence is a valid result.
- End with exactly: HYGIENE COMPLETE
"""

BUILTIN_PACKS = {
    "morning-briefing": MORNING_BRIEFING_PACK,
    "memory-hygiene": MEMORY_HYGIENE_PACK,
}

DEFAULT_JOBS = (
    {"name": "morning-briefing", "cron": "0 7 * * *",
     "mission": "@pack:morning-briefing"},
    {"name": "memory-hygiene", "cron": "0 9 * * 0",
     "mission": "@pack:memory-hygiene"},
)


def seed_packs(home: str | None = None, overwrite: bool = False) -> list[str]:
    """Write builtin packs that are missing. Returns created names."""
    d = packs_dir(home)
    _os.makedirs(d, exist_ok=True)
    created = []
    for name, body in BUILTIN_PACKS.items():
        p = _os.path.join(d, name + ".md")
        if _os.path.exists(p) and not overwrite:
            continue
        with open(p, "w") as f:
            f.write(body if body.endswith("\n") else body + "\n")
        created.append(name)
    return created


def ensure_defaults(home: str | None = None) -> dict:
    """Idempotent Hermes-gap install: seed packs + add missing schedule jobs.

    Existing packs and existing schedule jobs (possibly user-edited) are never
    overwritten. Returns {'packs': [...], 'jobs': [...]} of what was created.
    """
    from . import sched as sched_mod
    packs_created = seed_packs(home)
    jobs_created = []
    for spec in DEFAULT_JOBS:
        if any(j.get("name") == spec["name"] for j in sched_mod.load(home)):
            continue
        sched_mod.add(home, spec["name"], spec["cron"], spec["mission"])
        jobs_created.append(spec["name"])
    return {"packs": packs_created, "jobs": jobs_created}
