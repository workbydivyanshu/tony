"""tests/test_research.py — P13 RED: research fan-out helpers."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_module_exists():
    from lib import research  # noqa: F401


def test_angles():
    from lib import research
    prompts = research.explorer_prompts("quantum dots")
    assert len(prompts) == 3
    assert all("quantum dots" in p for p in prompts)
    assert len({p for p in prompts}) == 3  # distinct angles


def test_synthesis_prompt():
    from lib import research
    p = research.synthesis_prompt("quantum dots", ["FINDING A", "FINDING B"])
    assert "quantum dots" in p and "FINDING A" in p and "FINDING B" in p
    assert "URL" in p or "url" in p or "source" in p.lower()


def test_wave_cmds():
    from lib import research
    import tempfile
    import os
    d = tempfile.mkdtemp()
    rp = os.path.join(d, "r.md")
    cmds = research.wave_cmds(rp)
    assert len(cmds) == 2
    # F1: file must exist; F2: must contain >=3 http URLs -> simulate both
    open(rp, "w").write("a http://x.com b https://y.com http://z.com")
    import subprocess
    for c in cmds:
        assert subprocess.run(c, shell=True).returncode == 0, c
    # and F2 must fail with <3 URLs
    open(rp, "w").write("only http://one.com")
    assert subprocess.run(cmds[1], shell=True).returncode != 0
