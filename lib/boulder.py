"""boulder.py — fleet-format boulder read/write/parse. Stdlib only.

Format: # Boulder: <title> / ## TODOs (- [ ]/- [x]) /
## Final Verification Wave / ## Progress Log (append-only).
"""
import os
import re
import time


def new(title: str) -> dict:
    return {"title": title, "todos": [], "wave": [], "log": []}


def add_todo(b: dict, text: str, done: bool = False) -> None:
    b["todos"].append({"box": done, "text": text})


def add_wave(b: dict, text: str, done: bool = False) -> None:
    b["wave"].append({"box": done, "text": text})


def flip(b: dict, idx: int, done: bool, section: str = "todos") -> None:
    b[section][idx]["box"] = done


def log(b: dict, line: str) -> None:
    stamp = time.strftime("%Y-%m-%d %H:%M")
    b["log"].append(f"- {stamp}: {line}")


def _box(item: dict) -> str:
    return "- [x] " + item["text"] if item["box"] else "- [ ] " + item["text"]


def render(b: dict) -> str:
    lines = [f"# Boulder: {b['title']}", "## TODOs"]
    lines += [_box(t) for t in b["todos"]]
    lines += ["## Final Verification Wave"]
    lines += [_box(w) for w in b["wave"]]
    lines += ["## Progress Log"]
    lines += b["log"]
    return "\n".join(lines) + "\n"


def progress(b: dict) -> dict:
    """Return {done,total,waved,wavetotal,score,blocked} for a boulder."""
    todos = b.get("todos", [])
    wave = b.get("wave", [])
    done = sum(1 for t in todos if t["box"])
    total = len(todos)
    waved = sum(1 for w in wave if w["box"])
    wavetotal = len(wave)
    score = int(100 * (done + waved) / max(1, total + wavetotal))
    blocked = any("[BLOCKED]" in (t.get("text") or "") for t in todos)
    return {"done": done, "total": total, "waved": waved,
            "wavetotal": wavetotal, "score": score, "blocked": blocked}


_ROLE_PREFIX = r"(?:(\[role:\w+\])\s+)?"
_ITEM = re.compile(r"^-\s" + _ROLE_PREFIX + r"\[([xX]| )\]\s(.*)$")


def _parse_section(lines: list) -> list:
    out = []
    for ln in lines:
        m = _ITEM.match(ln.strip())
        if m:
            tag = (m.group(1) + " ") if m.group(1) else ""
            out.append({"box": (m.group(2) or "").lower() == "x",
                        "text": tag + m.group(3)})
    return out


def parse(text: str) -> dict:
    title, todos, wave, log = "", [], [], []
    section = None
    title_m = re.search(r"^# Boulder:\s*(.+)$", text, re.M)
    if title_m:
        title = title_m.group(1).strip()
    cur: list = []
    def flush():
        nonlocal todos, wave
        if section == "todos":
            todos = _parse_section(cur)
        elif section == "wave":
            wave = _parse_section(cur)
    for ln in text.splitlines():
        if ln.startswith("## TODOs"):
            flush()
            section = "todos"
            cur = []
        elif ln.startswith("## Final Verification Wave"):
            flush()
            section = "wave"
            cur = []
        elif ln.startswith("## Progress Log"):
            flush()
            section = "log"
            cur = []
        elif ln.startswith("#"):
            flush()
            section = None
            cur = []
        elif section in ("todos", "wave", "log"):
            cur.append(ln)
    flush()
    if section == "log":
        log = [line for line in cur if line.strip()]
    else:
        log = [line for line in text.split("## Progress Log", 1)[-1].splitlines()
               if line.strip()] if "## Progress Log" in text else []
    return {"title": title, "todos": todos, "wave": wave, "log": log}


def path_for(slug: str) -> str:
    d = os.path.join(os.path.expanduser("~"), ".tony", "boulders")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"{slug}.md")


def save(slug: str, b: dict) -> str:
    """Atomic write (P19b): tmp file + rename so a crash never truncates a
    boulder mid-write (the boulder is the mission ledger; corruption = loss)."""
    p = path_for(slug)
    tmp = p + ".tmp"
    with open(tmp, "w") as f:
        f.write(render(b))
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, p)
    return p


def load(path: str) -> dict:
    with open(path) as f:
        return parse(f.read())
