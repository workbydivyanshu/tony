"""skills.py — skill loader: discover ~/.tony/skills/*.md, match missions, inject
into the architect prompt. Stdlib only. Same doctrine as the fleet's 58 Cline
skills: a skill is a markdown file, first '# <name>' line is the name, body is
doctrine the planner must respect."""
import os
import re


def skills_dir() -> str:
    return os.path.join(os.path.expanduser("~"), ".tony", "skills")


def discover(path: str | None = None) -> list:
    """Read every *.md in the skills dir. Returns [{name, path, body}]."""
    d = path or skills_dir()
    if not os.path.isdir(d):
        return []
    out = []
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".md"):
            continue
        p = os.path.join(d, fn)
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError:
            continue
        m = re.search(r"^#\s+(.+)$", text, re.M)
        name = m.group(1).strip() if m else fn[:-3]
        out.append({"name": name, "path": p, "body": text.strip()})
    return out


def _keywords(text: str) -> set:
    raw = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", text)
    out = set()
    for tok in raw:
        out.add(tok.lower())
        out.update(p for p in re.split(r"[-_]", tok.lower()) if len(p) >= 3)
    return out


def match(mission: str, skills: list) -> list:
    """Keyword-overlap between mission text and skill name. >=1 shared keyword
    (>=4 chars, not a stopword) -> matched. Empty-dir/empty-mission -> []."""
    if not mission or not skills:
        return []
    stop = {"the", "and", "for", "with", "that", "this", "from", "into",
            "then", "when", "have", "must", "should"}
    mk = _keywords(mission)
    out = []
    for s in skills:
        sk = {w for w in _keywords(s["name"]) if len(w) >= 4 and w not in stop}
        if sk & mk:
            out.append(s)
    return out


def inject_prompt(base: str, matched: list) -> str:
    """Append matched skill doctrine to a prompt. Empty match -> base unchanged."""
    if not matched:
        return base
    block = "\nFleet skills relevant to this mission (respect their doctrine):\n"
    for s in matched:
        block += f"\n--- skill: {s['name']} ---\n{s['body']}\n"
    return base + block
