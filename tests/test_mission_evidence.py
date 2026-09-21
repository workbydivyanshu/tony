"""P38 evidence pins: fold rule, critic child-lines, tag precedence,
mission_fn-None hold, resume re-dispatch, architect workdir-LAST.

Rewritten 2026-09-21 to the P38 plan (prior draft contradicted it:
75/40 thresholds vs plan D4 60-rule; hasattr-on-function pins;
invented engine.re_dispatch API). Rationale logged in NOTEPAD P38.
Engine-path pins (None-hold, resume) go GREEN in the dispatch wave.
"""
import os
import sys
import inspect

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── 1. fold threshold: >=60 done, else BLOCKED (plan D4) ─────────────

def test_fold_threshold_child_score_75_done():
    """lib.fold.fold_threshold: 75 -> done."""
    from lib.fold import fold_threshold
    assert fold_threshold(child_score=75) == "done"


def test_fold_threshold_child_score_60_done():
    """Boundary: exactly 60 -> done."""
    from lib.fold import fold_threshold
    assert fold_threshold(child_score=60) == "done"


def test_fold_threshold_child_score_40_blocked():
    """Below 60 -> BLOCKED (no partial credit)."""
    from lib.fold import fold_threshold
    assert fold_threshold(child_score=40) == "BLOCKED"


def test_fold_done_threshold_constant():
    """DONE_THRESHOLD == 60 (single threshold, plan D4)."""
    from lib import fold
    assert fold.DONE_THRESHOLD == 60


# ── 2. critic CHILD section rendering with truncation ────────────────

def test_critic_child_render_truncation():
    """lib.critic_verdict.child_render caps length with CHILD marker."""
    from lib.critic_verdict import child_render
    result = child_render("some boulder content", max_len=80)
    assert "CHILD" in result
    assert len(result) <= 80, f"expected truncation at 80, got {len(result)}"


def test_critic_child_truncate_len_constant():
    """TRUNCATE_LEN exists for the cap."""
    from lib import critic_verdict
    assert isinstance(critic_verdict.TRUNCATE_LEN, int)


# ── 3. mission-tag-beats-role-tag precedence ─────────────────────────

def test_mission_tag_beats_role_tag():
    """A TODO carrying both tags dispatches as mission, not role."""
    from lib import missiontags
    kind, name = missiontags.resolve_tag("[mission:deploy-api] [role:builder]")
    assert (kind, name) == ("mission", "deploy-api"), (kind, name)


def test_role_tag_alone_dispatches_role():
    """Role-only TODO stays a role dispatch."""
    from lib import missiontags
    kind, name = missiontags.resolve_tag("[role:explorer] map auth")
    assert (kind, name) == ("role", "explorer"), (kind, name)


def test_plain_todo_defaults_builder():
    """Untagged TODO defaults to builder (existing convention)."""
    from lib import missiontags
    kind, name = missiontags.resolve_tag("fix typo")
    assert (kind, name) == ("role", "builder"), (kind, name)


# ── 6. architect_prompt keeps workdir LAST (P34 regression pin) ──────

def test_architect_prompt_workdir_last_param():
    """workdir must remain the last parameter."""
    from lib import roles
    params = list(inspect.signature(roles.architect_prompt).parameters.keys())
    assert params[-1] == "workdir", f"workdir must be last, got {params[-1]}"


def test_architect_prompt_positional_compat():
    """Existing positional call shape still binds (mission + 3 optionals)."""
    from lib import roles
    sig = inspect.signature(roles.architect_prompt)
    bound = sig.bind_partial("mission", None, None, None)
    assert "workdir" not in bound.arguments, bound.arguments
