"""tests/test_waveguard_moves.py — P29 destructive-move probe.

Probed 2026-09-20 directly against check() (strings only, never executed).
KEPT (slipped through pre-fix, pinned below): mass moves (mv /*, mv-to-
/dev/null incl $HOME/~/work forms), find -delete, symlink to dotfile or
/dev/null, shell redirect into home dotfiles.
OUT OF SCOPE (documented, not pinned): cp/tar/zip/cat reads (exfiltration
is a sandbox problem — the deny-list guards destruction, per module
docstring); chmod/chown without root target (mode churn, recoverable via
git); obfuscated interpreter payloads (chr-concat et al — uncatchable by
regex without security theater); plain `mv old new` renames (harmless,
conceivably legitimate).
BENIGN (allowed pre- and post-fix, precision anchor): plain renames, find
without -delete, redirect to /tmp, cat.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib import waveguard as w

# Verified 2026-09-20: check() ALLOWS every one of these pre-fix.
HOSTILE = [
    "mv /* /tmp/x",
    "mv /home/divyu/work/* /dev/null",
    "mv work/* /tmp/",
    "mv ~/docs /dev/null",
    "mv $HOME/a /dev/null",
    "find work -delete",
    "find / -name x -delete",
    "ln -sf /dev/null ~/.bashrc",
    "echo hi > ~/.bashrc",
]

# Precision anchor: harmless shapes the new patterns must NOT catch.
BENIGN = [
    "mv old.txt new.txt",
    "find work -name x",
    "echo ok > /tmp/tony-out.txt",
    "cat file.txt",
    "test -f hello.txt",
]


def test_moves_hostile_blocked():
    """Every probed destructive move must be blocked post-fix."""
    for cmd in HOSTILE:
        safe, reason = w.check(cmd)
        assert not safe, f"slip still allowed: {cmd!r} ({reason})"


def test_moves_benign_allowed():
    """Renames, find-without-delete, /tmp redirects stay allowed."""
    for cmd in BENIGN:
        safe, reason = w.check(cmd)
        assert safe, f"false positive: {cmd!r} ({reason})"
