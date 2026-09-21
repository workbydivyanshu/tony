"""workdir — resolve work directories and detect foreign paths.

All paths are resolved against ~/.tony/work (DEFAULT_ROOT),
which is expanded at call time via expanduser, never at import time.
"""
import os

DEFAULT_ROOT_SEG = (".tony", "work")


def _default_root() -> str:
    """~/.tony/work resolved at CALL time (tests redirect HOME)."""
    return os.path.join(os.path.expanduser("~"), *DEFAULT_ROOT_SEG)


def resolve(explicit: str | None, slug: str) -> str:
    """Return the work directory path for a given slug.

    If explicit is None, returns ~/.tony/work/<slug>.
    If explicit is a string, returns abspath(explicit) — pure, no mkdir.
    """
    if explicit is None:
        return os.path.join(_default_root(), slug)
    return os.path.abspath(explicit)


def is_foreign(path: str) -> bool:
    """Return True when path is outside ~/.tony/work.

    Separator-aware: ~/.tony/work-evil is foreign (prefix match alone
    would wrongly call it local).
    """
    root = os.path.abspath(_default_root())
    return os.path.commonpath([root, os.path.abspath(path)]) != root
