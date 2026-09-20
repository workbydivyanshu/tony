"""P-next RED proof: plan-gate must exist (confirm before any builder call)."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib import plangate

def _boom(_prompt=""):
    raise AssertionError("input must not fire when pre-approved or headless")

def test_yes_skips_prompt():
    b = {"todos": [{"box": False, "text": "1. x"}], "wave": [], "log": []}
    assert plangate.confirm_plan(b, input_fn=_boom, is_tty=True, pre_approved=True) is True
    assert any("--yes" in l for l in b["log"])

def test_headless_skips_no_hang():
    b = {"todos": [{"box": False, "text": "1. x"}], "wave": [], "log": []}
    assert plangate.confirm_plan(b, input_fn=_boom, is_tty=False, pre_approved=False) is True
    assert any("non-TTY" in l for l in b["log"])

def test_tty_yes_proceeds():
    b = {"todos": [{"box": False, "text": "1. x"}], "wave": [], "log": []}
    assert plangate.confirm_plan(b, input_fn=lambda _p="": "y", is_tty=True, pre_approved=False) is True

def test_tty_empty_declines():
    b = {"todos": [{"box": False, "text": "1. x"}], "wave": [], "log": []}
    assert plangate.confirm_plan(b, input_fn=lambda _p="": "", is_tty=True, pre_approved=False) is False
    assert any("declined" in l for l in b["log"])

def test_tty_no_declines():
    b = {"todos": [{"box": False, "text": "1. x"}], "wave": [], "log": []}
    assert plangate.confirm_plan(b, input_fn=lambda _p="": "n", is_tty=True, pre_approved=False) is False
