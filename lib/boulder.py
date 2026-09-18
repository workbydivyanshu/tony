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


_ITEM = re.compile(r"^-\s\[( |x)\]\s(.*)$")


def _parse_section(lines: list) -> list:
    out = []
    for ln in lines:
        m = _ITEM.match(ln.strip())
        if m:
            out.append({"box": m.group(1) == "x", "text": m.group(2)})
    return out


def parse(text: str) -> dict:
    title, todos, wave, log = "", [], [], []
    section = None
    title_m = re.search(r"^# Boulder:\s*(.+)$", text, re.M)
    if title_m:
        title = title_m.group(1).strip()
    cur = []
    def flush():
        nonlocal todos, wave
        if section == "todos":
            todos = _parse_section(cur)
        elif section == "wave":
            wave = _parse_section(cur)
    for ln in text.splitlines():
        if ln.startswith("## TODOs"):
            flush(); section = "todos"; cur = []
        elif ln.startswith("## Final Verification Wave"):
            flush(); section = "wave"; cur = []
        elif ln.startswith("## Progress Log"):
            flush(); section = "log"; cur = []
        elif ln.startswith("#"):
            flush(); section = None; cur = []
        elif section in ("todos", "wave", "log"):
            cur.append(ln)
    flush()
    if section == "log":
        log = [l for l in cur if l.strip()]
    else:
        log = [l for l in text.split("## Progress Log", 1)[-1].splitlines() if l.strip()] \
            if "## Progress Log" in text else []
    return {"title": title, "todos": todos, "wave": wave, "log": log}


def path_for(slug: str) -> str:
    d = os.path.join(os.path.expanduser("~"), ".tony", "boulders")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"{slug}.md")


def save(slug: str, b: dict) -> str:
    p = path_for(slug)
    with open(p, "w") as f:
        f.write(render(b))
    return p


def load(path: str) -> dict:
    with open(path) as f:
        return parse(f.read())
