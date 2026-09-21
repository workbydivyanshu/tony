"""fold.py — child score fold rule for mission evidence (plan D4).

One threshold: score >= DONE_THRESHOLD folds to done, anything below
folds to BLOCKED. No partial credit, no middle zone."""

DONE_THRESHOLD = 60


def fold_threshold(child_score: int) -> str:
    """Fold a child score into done/BLOCKED (plan D4: no partial credit)."""
    if child_score >= DONE_THRESHOLD:
        return "done"
    return "BLOCKED"
