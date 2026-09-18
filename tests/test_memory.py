"""P8 RED proof: lib/memory must exist with remember/recall/forget + prompt injection."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib import memory, roles

def test_remember_recall_forget(tmp_home="/tmp/tony-test-memory"):
    import shutil
    shutil.rmtree(tmp_home, ignore_errors=True)
    os.environ["_TONY_TEST_HOME"] = tmp_home
    p = memory.remember("probe fact alpha", home=tmp_home)
    assert os.path.exists(p), p
    hits = memory.recall("alpha", home=tmp_home)
    assert any("probe fact alpha" in h for h in hits), hits
    n = memory.forget("alpha", home=tmp_home)
    assert n >= 1, n
    assert not any("probe fact alpha" in h for h in memory.recall(home=tmp_home)), "forget failed"
    shutil.rmtree(tmp_home, ignore_errors=True)

def test_architect_prompt_carries_memory():
    prompt = roles.architect_prompt("dummy mission", ["context7"], memory_lines=["- 2026-09-18 — probe"])
    assert "probe" in prompt, prompt[:200]
