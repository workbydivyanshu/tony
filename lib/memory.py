"""memory.py — persistent self across missions (Hermes-replacement step 1). Stdlib only.

~/.tony/memory/MEMORY.md, append-only, one fact per line:
  - YYYY-MM-DD — fact
recall() filters case-insensitive; forget() removes by substring.
"""
import os
import time


def mem_dir(home: str | None = None) -> str:
    base = home or os.path.expanduser("~")
    return os.path.join(base, ".tony", "memory")


def mem_path(home: str | None = None) -> str:
    return os.path.join(mem_dir(home), "MEMORY.md")


def remember(fact: str, home: str | None = None) -> str:
    """Append one dated fact line. Returns the file path."""
    fact = (fact or "").strip()
    if not fact:
        raise ValueError("remember: empty fact")
    d = mem_dir(home)
    os.makedirs(d, exist_ok=True)
    p = mem_path(home)
    stamp = time.strftime("%Y-%m-%d")
    with open(p, "a") as f:
        f.write(f"- {stamp} — {fact}\n")
    return p


def recall(query: str | None = None, home: str | None = None,
           limit: int = 50) -> list:
    """All lines (or case-insensitive substring matches), oldest first, capped."""
    p = mem_path(home)
    try:
        with open(p) as f:
            lines = [ln.rstrip("\n") for ln in f if ln.strip()]
    except FileNotFoundError:
        return []
    if query:
        q = query.lower()
        lines = [ln for ln in lines if q in ln.lower()]
    return lines[-limit:]


def forget(substr: str, home: str | None = None) -> int:
    """Remove lines containing substr (case-insensitive). Returns count removed.

    P19b: empty/whitespace substring is a NO-OP, never a wipe (it used to
    match every line and erase the entire memory file)."""
    if not (substr or "").strip():
        return 0
    p = mem_path(home)
    try:
        with open(p) as f:
            lines = [ln for ln in f]
    except FileNotFoundError:
        return 0
    q = substr.lower()
    kept = [ln for ln in lines if q not in ln.lower()]
    removed = len(lines) - len(kept)
    if removed:
        with open(p, "w") as f:
            f.writelines(kept)
    return removed
