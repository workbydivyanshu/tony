"""tests/test_skills.py — P12 RED: skill loader must not exist yet (import fails)."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_skills_module_exists():
    from lib import skills  # noqa: F401  # RED until lib/skills.py lands


def test_discover_and_match():
    from lib import skills
    found = skills.discover("/nonexistent-skills-dir")
    assert found == []


def test_discover_reads_dir(tmpdir="/tmp/tony-test-skills"):
    import shutil
    from lib import skills
    shutil.rmtree(tmpdir, ignore_errors=True)
    os.makedirs(tmpdir)
    with open(os.path.join(tmpdir, "apple.md"), "w") as f:
        f.write("# Apple Doctrine\nShip HIG polish.\n")
    with open(os.path.join(tmpdir, "notes.txt"), "w") as f:
        f.write("not a skill\n")
    found = skills.discover(tmpdir)
    assert len(found) == 1, found
    assert found[0]["name"] == "Apple Doctrine"
    assert "HIG polish" in found[0]["body"]


def test_match_keywords(tmpdir="/tmp/tony-test-skills2"):
    import shutil
    from lib import skills
    shutil.rmtree(tmpdir, ignore_errors=True)
    os.makedirs(tmpdir)
    with open(os.path.join(tmpdir, "a.md"), "w") as f:
        f.write("# config-parser doctrine\nRespect the parser.\n")
    with open(os.path.join(tmpdir, "b.md"), "w") as f:
        f.write("# guitar setup\nStrings and tuning.\n")
    found = skills.discover(tmpdir)
    hit = skills.match("rewrite the config parser for speed", found)
    assert [s["name"] for s in hit] == ["config-parser doctrine"], hit
    assert skills.match("", found) == []


def test_inject_prompt(tmpdir="/tmp/tony-test-skills3"):
    import shutil
    from lib import skills
    shutil.rmtree(tmpdir, ignore_errors=True)
    os.makedirs(tmpdir)
    with open(os.path.join(tmpdir, "a.md"), "w") as f:
        f.write("# config rules\nNever touch the parser.\n")
    hit = skills.match("fix config rules", skills.discover(tmpdir))
    out = skills.inject_prompt("BASE", hit)
    assert out.startswith("BASE") and "Never touch the parser" in out
    assert skills.inject_prompt("BASE", []) == "BASE"
