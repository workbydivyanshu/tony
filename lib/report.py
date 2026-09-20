"""report.py — scribe: final report + MISSION SCORE. Stdlib only."""
import os
import time


def write(outdir: str, slug: str, mission: str, models_used: dict,
          b: dict, score: int, costs: str) -> str:
    os.makedirs(outdir, exist_ok=True)
    done = [t for t in b["todos"] if t["box"]]
    waved = [w for w in b["wave"] if w["box"]]
    lines = [
        f"# Tony report: {slug}",
        f"Date: {time.strftime('%Y-%m-%d %H:%M')}",
        f"Mission: {mission}",
        "",
        "## Models used",
    ]
    lines += [f"- {r}: {m}" for r, m in models_used.items()]
    lines += ["", f"## TODOs ({len(done)}/{len(b['todos'])})"]
    lines += [f"- [{'x' if t['box'] else ' '}] {t['text']}" for t in b["todos"]]
    lines += ["", f"## Verification wave ({len(waved)}/{len(b['wave'])})"]
    lines += [f"- [{'x' if w['box'] else ' '}] {w['text']}" for w in b["wave"]]
    lines += ["", "## Progress log"]
    lines += b["log"]
    lines += ["", f"MISSION SCORE: {score}/100 — {costs}"]
    p = os.path.join(outdir, f"tony-{slug}.md")
    with open(p, "w") as f:
        f.write("\n".join(lines) + "\n")
    return p
