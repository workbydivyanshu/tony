"""P1 RED proof: catalog parse + tier assignment must exist."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib import catalog, tiers

SAMPLE = """opencode/big-pickle
opencode/ling-3.0-flash-fin-free
opencode/mimo-v2.5-free
opencode/muse-spark-1.2-contributor-free
opencode/muse-spark-1.3-contributor-free
opencode/nemotron-3-ultra-free
opencode/nemotron-3.5-lightning-free
"""

def test_parse_models():
    got = catalog.parse_models(SAMPLE)
    assert got == sorted(SAMPLE.split()), f"parse mismatch: {got}"

def test_tier_assignment():
    models = sorted(SAMPLE.split())
    heavy = tiers.pick(models, "heavy")
    fast = tiers.pick(models, "fast")
    assert heavy[0] == "opencode/nemotron-3-ultra-free", heavy
    assert fast[0] == "opencode/nemotron-3.5-lightning-free", fast

def test_roles():
    m = tiers.assign_roles(sorted(SAMPLE.split()))
    assert m["architect"] == "opencode/nemotron-3-ultra-free", m
    assert m["scribe"] == "opencode/nemotron-3.5-lightning-free", m
