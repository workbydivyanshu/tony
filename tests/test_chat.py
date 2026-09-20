"""P9 RED proof: lib/chat history + prompt + REPL control must exist."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib import chat

def test_history_round_trip(tmp_home="/tmp/tony-test-chat"):
    import shutil
    shutil.rmtree(tmp_home, ignore_errors=True)
    chat.append("s1", "user", "hello tony", home=tmp_home)
    chat.append("s1", "tony", "hello vianca", home=tmp_home)
    hist = chat.load("s1", home=tmp_home)
    assert len(hist) == 2 and hist[0]["role"] == "user", hist
    prompt = chat.build_prompt("how are you", hist, memory_lines=["- 2026-09-18 — probe"])
    assert "hello tony" in prompt and "probe" in prompt and "how are you" in prompt, prompt[:200]
    shutil.rmtree(tmp_home, ignore_errors=True)

def test_repl_control(tmp_home="/tmp/tony-test-chat-repl"):
    import shutil
    shutil.rmtree(tmp_home, ignore_errors=True)
    inputs = iter(["", "hi", "/quit"])
    outputs = []
    calls = []
    def fake_call(prompt):
        calls.append(prompt)
        return "hey there"
    chat.repl("s2", home=tmp_home, input_fn=lambda _: next(inputs),
              output_fn=outputs.append, call_fn=fake_call)
    assert len(calls) == 1 and "user: hi" in calls[0], calls
    assert any("hey there" in o for o in outputs), outputs
    assert len(chat.load("s2", home=tmp_home)) == 2
    shutil.rmtree(tmp_home, ignore_errors=True)
