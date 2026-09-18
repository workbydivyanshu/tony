"""watch.py — pure render_snapshot + tiny I/O helpers. Stdlib only.

No curses, no Textual. render_snapshot produces text panes from a boulder
dict, a runs tail, work files, and assignments.
"""
import os


def _truncate(line: str, maxlen: int = 200) -> str:
    return line[:maxlen]


def render_snapshot(b: dict, runs_tail: list, work_files: list,
                    assignments: dict | None) -> str:
    """Render a boulder into text panes. Stdlib only, no curses/Textual.

    Panes: TODOs, wave, runs, roster. Headers contain the contract
    substrings: 'TODO'/'TODOs', 'ave' (wave), 'un' (runs), 'oster' (roster).
    Every output line is truncated to <=200 chars.
    """
    from .boulder import progress

    p = progress(b)
    lines: list = []

    # --- TODOs pane ---
    lines.append(f"TODOs: {p['done']}/{p['total']}")
    for t in b.get("todos", []):
        box = "- [x] " if t["box"] else "- [ ] "
        lines.append(_truncate(box + t.get("text", "")))

    # --- wave pane ---
    lines.append(f"wave: {p['waved']}/{p['wavetotal']}")
    for w in b.get("wave", []):
        box = "- [x] " if w["box"] else "- [ ] "
        lines.append(_truncate(box + w.get("text", "")))

    # --- runs pane ---
    lines.append(f"runs: {len(runs_tail)}")
    if runs_tail:
        for r in runs_tail:
            lines.append(_truncate(str(r)))
    else:
        lines.append("(no runs)")

    # --- roster pane ---
    lines.append("roster:")
    if assignments:
        for role, model in assignments.items():
            lines.append(_truncate(f"  {role}: {model}"))
    else:
        lines.append("  (empty)")

    # --- work_files pane ---
    lines.append("work_files:")
    if work_files:
        for wf in work_files:
            lines.append(_truncate(f"  {wf}"))
    else:
        lines.append("  (none)")

    return "\n".join(lines) + "\n"


def tail_lines(path: str, n: int) -> list:
    """Return the last n lines of a file as a list. Empty file -> [].

    Stdlib only, no third-party imports.
    """
    try:
        with open(path) as f:
            all_lines = f.readlines()
        return all_lines[-n:] if n > 0 else []
    except OSError:
        return []


def work_files(workdir: str) -> list:
    """Return sorted list of .md files in workdir. Stdlib only."""
    try:
        return sorted(f for f in os.listdir(workdir) if f.endswith(".md"))
    except OSError:
        return []
