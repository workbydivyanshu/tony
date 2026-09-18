"""tiers.py — pattern-based tier assignment + role map. Ported from fleet-models-sync.

Patterns, never ids: renames and churn self-heal. Unknown models -> spare tier.
"""
import re
import sys

# tier -> ordered id patterns, best first (from scripture Ch.3)
TIERS = {
    "heavy":    [r"nemotron-3-ultra", r"muse-spark-1\.3", r"big-pickle", r"union-alpha"],
    "research": [r"muse-spark-1\.3", r"nemotron-3-ultra", r"muse-spark-1\.2", r"union-alpha"],
    "fast":     [r"nemotron-3\.5-lightning", r"ling-3\.0-flash", r"mimo-v2\.5", r"muse-spark-1\.2"],
}

# role -> (tier, effort)
ROLES = {
    "architect":  ("heavy", "max"),
    "builder":    ("heavy", "xhigh"),
    "researcher": ("research", "xhigh"),
    "critic":     ("research", "xhigh"),
    "explorer":   ("fast", "high"),
    "scribe":     ("fast", "low"),
}


def match(model_id: str, patterns: list) -> int:
    for rank, pat in enumerate(patterns):
        if re.search(pat, model_id):
            return rank
    return 99


def pick(catalog: list, tier: str, exclude: tuple = ()) -> list:
    cands = [m for m in catalog if match(m, TIERS[tier]) < 99 and m not in exclude]
    return sorted(cands, key=lambda m: match(m, TIERS[tier]))


def spare(catalog: list) -> list:
    """Models matching no tier -> last-resort fallback."""
    known = set()
    for tier in TIERS:
        known.update(pick(catalog, tier))
    return sorted(set(catalog) - known)


def resolve_override(catalog: list, pattern: str):
    """First catalog model matching *pattern* via re.search, or None."""
    for m in catalog:
        if re.search(pattern, m):
            return m
    return None


def assign_roles_with_sources(catalog: list, overrides=None):
    """role -> model with source tracking.

    overrides=None  -> legacy format {role: model_id}  (byte-identical to old assign_roles).
    overrides=dict  -> enriched format {role: {"model": model_id, "source": ...}}.
    """
    if overrides is None:
        out = {}
        for role, (tier, _effort) in ROLES.items():
            picks = pick(catalog, tier)
            if not picks:
                fb = spare(catalog)
                if not fb:
                    raise RuntimeError(f"no model available for role {role}")
                out[role] = fb[0]
            else:
                out[role] = picks[0]
        return out
    out = {}
    for role, (tier, _effort) in ROLES.items():
        pattern = overrides.get(role)
        if pattern is not None:
            model = resolve_override(catalog, pattern)
            if model is not None:
                out[role] = {"model": model, "source": "override"}
                continue
            print(
                f"tony: role '{role}' pattern '{pattern}' matched nothing live; "
                "falling back to tier default",
                file=sys.stderr,
            )
        picks = pick(catalog, tier)
        if not picks:
            fb = spare(catalog)
            if not fb:
                continue
            out[role] = {"model": fb[0], "source": "tier-default"}
        else:
            out[role] = {"model": picks[0], "source": "tier-default"}
    return out


def assign_roles(catalog: list) -> dict:
    """role -> best model id. Raises if a role's tier is empty."""
    return assign_roles_with_sources(catalog, None)


def tier_map(catalog: list) -> dict:
    return {tier: pick(catalog, tier) for tier in TIERS} | {"spare": spare(catalog)}
