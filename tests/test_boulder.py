"""P2 RED proof: fleet-format boulder read/write/parse must exist."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib import boulder

SAMPLE = """# Boulder: test slug
## TODOs
- [ ] 1. First thing
- [x] 2. Done thing
## Final Verification Wave
- [ ] F1. must pass
## Progress Log
- t0: started
"""

def test_round_trip():
    b = boulder.parse(SAMPLE)
    assert b["title"] == "test slug", b
    assert len(b["todos"]) == 2
    assert b["todos"][0] == {"box": False, "text": "1. First thing"}, b["todos"][0]
    assert b["todos"][1]["box"] is True
    assert len(b["wave"]) == 1 and b["wave"][0]["text"].startswith("F1.")
    boulder.flip(b, 0, True)
    assert b["todos"][0]["box"] is True
    out = boulder.render(b)
    b2 = boulder.parse(out)
    assert b2["todos"][0]["box"] is True, "render must survive re-parse"

def test_new_and_log():
    b = boulder.new("my slug")
    boulder.add_todo(b, "do the thing")
    boulder.add_wave(b, "prove the thing")
    boulder.log(b, "a thing happened")
    out = boulder.render(b)
    assert "- [ ] do the thing" in out
    assert "- [ ] prove the thing" in out
    assert "a thing happened" in out

ARCHITECT_TAGGED = """# Boulder: tony-parallel-recon
## TODOs
- [role:explorer] [ ] 1. List all files in ~/tony/lib directory
- [role:explorer] [ ] 2. Read boulder format from ~/tony/lib/boulder.py header
- [role:builder] [ ] 3. Write hello-par.txt with exact content
- [role:builder] [x] 4. Already verified thing
## Final Verification Wave
- [ ] F1. test -f /home/divyu/tony-e2e-par/hello-par.txt
## Progress Log
"""

def test_parse_role_tag_before_box():
    # Live parallel-e2e proof: the architect emits tags BEFORE the box
    # (roles.py orders it so). The parser must accept that order, keep the
    # tag in text for dispatch, and render box-first fleet format.
    import sys as _s
    _s.path.insert(0, ".")
    from lib import engine as _eng
    b = boulder.parse(ARCHITECT_TAGGED)
    assert len(b["todos"]) == 4, b["todos"]
    assert b["todos"][0]["text"].startswith("[role:explorer]"), b["todos"][0]
    assert b["todos"][3]["box"] is True
    assert [_eng.todo_role(t["text"]) for t in b["todos"]] == [
        "explorer", "explorer", "builder", "builder"]
    out = boulder.render(b)
    assert out.count("## TODOs") == 1, "no duplicated sections"
    b2 = boulder.parse(out)
    assert len(b2["todos"]) == 4, "render must survive re-parse"
    assert [_eng.todo_role(t["text"]) for t in b2["todos"]] == [
        "explorer", "explorer", "builder", "builder"]
