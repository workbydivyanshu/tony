"""tests/test_p15.py — P15 RED: critic verdict parse + chat skill injection."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_module():
    from lib import critic_verdict  # noqa: F401


def test_verdict_parse():
    from lib import critic_verdict as cv
    assert cv.parse("VERDICT: PASS\nall good") == "PASS"
    assert cv.parse("verdict: issues: thing missing") == "ISSUES"
    assert cv.parse("blah ISSUES in rubric text VERDICT: PASS") == "PASS"
    assert cv.parse("no verdict line at all") is None
    assert cv.parse("VERDICT: PASS-after-fix") == "PASS-after-fix"


def test_verdict_first_hit_beats_transcript():
    # live-proven failure mode (P15): stale 'Verdict: PASS' from a transcript
    # the critic read AFTER its own verdict must not flip ISSUES -> PASS.
    from lib import critic_verdict as cv
    poisoned = ("findings...\nVERDICT: ISSUES\nEVIDENCE: missing\n"
                "> transcript...\n$ cat NOTEPAD.md\n"
                "- Verdict: PASS unconditional, 0 ISSUES, 8 notes.\n")
    assert cv.parse(poisoned) == "ISSUES"
    assert cv.is_issues(poisoned) is True


def test_chat_prompt_with_skills(tmpdir="/tmp/tony-test-chat-skills"):
    import shutil
    from lib import chat, skills
    shutil.rmtree(tmpdir, ignore_errors=True)
    os.makedirs(tmpdir)
    with open(os.path.join(tmpdir, "s.md"), "w") as f:
        f.write("# tone rules\nBe terse.\n")
    hit = skills.match("tone rules for the fleet", skills.discover(tmpdir))
    out = chat.build_prompt("hello", [], matched_skills=hit)
    assert "Be terse." in out
    assert chat.build_prompt("hello", []) == chat.build_prompt("hello", [])
