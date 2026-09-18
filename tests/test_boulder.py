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
