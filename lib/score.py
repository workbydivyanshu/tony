"""score.py — wave-gated weighted score computation. Pure module, stdlib only.

Formula: 40*todo_frac + 40*wave_frac + 20*critic_bonus, rounded int.
Caps: empty wave list caps total at 40; any TODO containing [BLOCKED] caps at 49;
gate==ISSUES zeroes the bonus; gate==N/A grants 10 (not 20).
Score is always in [0,100].
"""


def compute(b: dict, gate: str) -> dict:
    todos = b.get("todos", [])
    wave = b.get("wave", [])

    total = len(todos)
    wavetotal = len(wave)
    done = sum(1 for t in todos if t["box"])
    waved = sum(1 for w in wave if w["box"])

    todo_frac = done / total if total > 0 else 0.0
    wave_frac = waved / wavetotal if wavetotal > 0 else 0.0

    # Determine critic bonus
    if gate == "ISSUES":
        critic_bonus = 0.0
    elif gate == "N/A":
        critic_bonus = 0.5
    else:
        critic_bonus = 1.0

    score = round(40 * todo_frac + 40 * wave_frac + 20 * critic_bonus)

    # No progress at all -> 0 regardless of gate (bonus must not lift a blank run)

    # Apply caps
    capped = False
    if todo_frac == 0.0 and wave_frac == 0.0:
        score = 0
    if wavetotal == 0:
        score = min(score, 40)
        capped = True
    if any("[BLOCKED]" in (t.get("text") or "") for t in todos):
        score = min(score, 49)
        capped = True

    score = max(0, min(100, score))

    return {
        "score": score,
        "todo_frac": todo_frac,
        "wave_frac": wave_frac,
        "critic_bonus": int(20 * critic_bonus),
        "capped": capped,
    }
