"""test_foreign_safety.py — foreign-repo prompt doctrine safety tests.

Plain asserts, zero model calls. Confirms that architect_prompt and
BUILDER_SYSTEM enforce the no-commit/no-push boundary for foreign
workdirs and that the default prompt stays byte-identical.
"""
from lib.roles import BUILDER_SYSTEM, architect_prompt

_MISSION = "create a file in the repo"


def test_workdir_output_contains_path_and_target_directive():
    """(a) architect_prompt with workdir must contain the path and a TARGET DIRECTORY line."""
    out = architect_prompt(_MISSION, workdir="/x/repo")
    assert "/x/repo" in out
    assert "TARGET DIRECTORY" in out


def test_default_output_byte_identical_to_workdir_none():
    """(b) Default architect_prompt(mission) must equal architect_prompt(mission, workdir=None)."""
    default = architect_prompt(_MISSION)
    explicit_none = architect_prompt(_MISSION, workdir=None)
    assert default == explicit_none
    assert "TARGET DIRECTORY" not in default


def test_builder_system_has_git_commit_prohibition():
    """(c) BUILDER_SYSTEM must prohibit git commits."""
    assert "git commit" in BUILDER_SYSTEM.lower()


def test_builder_system_has_git_push_prohibition():
    """(c) BUILDER_SYSTEM must prohibit git push."""
    assert "push" in BUILDER_SYSTEM.lower()


def test_foreign_workdir_has_no_commit_no_push_doctrine():
    """(d) Foreign workdir output must contain no-commit/no-push doctrine."""
    out = architect_prompt(_MISSION, workdir="/x/repo")
    assert "Do not run git commit/push/add/reset" in out
    assert "leave the tree uncommitted" in out
