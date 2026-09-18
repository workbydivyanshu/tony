"""config.py — ~/.tony/config.json read/write. Stdlib only.

$HOME resolved at call time (tests redirect HOME). No import-time constant.
"""
import json
import os
import re
import sys

from lib import tiers


def config_path() -> str:
    """$HOME resolved at CALL time — never import-time constant."""
    return os.path.join(os.path.expanduser("~"), ".tony", "config.json")


def _defaults() -> dict:
    return {"roles": {}}


def load() -> dict:
    """Read config.json. Missing → defaults. Bad JSON → stderr warning + defaults."""
    try:
        with open(config_path()) as f:
            return json.load(f)
    except FileNotFoundError:
        return _defaults()
    except json.JSONDecodeError as exc:
        print(f"config: corrupt {config_path()}: {exc}", file=sys.stderr)
        return _defaults()


def save(cfg: dict) -> None:
    """Atomically write config.json, creating dirs as needed."""
    p = config_path()
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        json.dump(cfg, f, indent=2)


def get_roles() -> dict:
    return load().get("roles", {})


def set_role(role: str, pattern: str) -> None:
    """Set a role's regex pattern. Validates role name + regex at call time."""
    if role not in tiers.ROLES:
        raise KeyError(f"unknown role: {role!r}")
    re.compile(pattern)  # fail-fast on bad regex
    cfg = load()
    cfg.setdefault("roles", {})[role] = pattern
    cfg.setdefault("opencode_bin", "opencode")
    save(cfg)


def clear_role(role: str) -> None:
    """Remove a role. No-op if missing."""
    cfg = load()
    cfg.get("roles", {}).pop(role, None)
    save(cfg)


def clear_roles() -> None:
    """Empty roles dict, preserve all other keys."""
    cfg = load()
    cfg["roles"] = {}
    save(cfg)


def validate(catalog: list) -> list:
    """Return one warning per role whose pattern matches nothing in catalog."""
    warnings = []
    for role, (_tier, _effort) in tiers.ROLES.items():
        pattern = get_roles().get(role)
        if pattern is None:
            continue
        if not any(re.search(pattern, m) for m in catalog):
            warnings.append(f"role {role!r}: pattern {pattern!r} matches no model in catalog")
    return warnings
