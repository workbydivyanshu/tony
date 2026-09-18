"""roles.py — role definitions + architect prompt template. Stdlib only.

Roles ride tiers (tiers.py); the architect emits boulder-format plans.
"""
from . import tiers

ARCHITECT_SYSTEM = """You are planning ONLY. No code, no execution, no prose outside the format.
Break the mission into 3-7 concrete TODOs and 2-4 Final Verification commands.
Verification commands must be shell commands that objectively pass or fail.
Prefix EVERY TODO line with a role tag [role:<name>] choosing from:
builder (default — code changes, file writes, sequential), explorer (read-only
recon: find/show/describe, NEVER writes — these run concurrently via threads),
researcher (external docs/synthesis, sequential). When in doubt use builder.
Emit the boulder markdown EXACTLY in this shape and nothing else:

# Boulder: <short slug-friendly title>
## TODOs
- [ ] 1. <concrete step one>
- [ ] 2. <concrete step two>
## Final Verification Wave
- [ ] F1. <shell command>
## Progress Log
(empty — the engine fills this in)
"""

BUILDER_SYSTEM = """You execute ONE assigned TODO from a boulder. Bounded change, no scope creep.
When done, report: files changed, verification output, verdict. Never claim done
from inference — only from captured command output."""


def role_model(role: str, assignments: dict) -> str:
    return assignments[role]


def role_effort(role: str) -> str:
    return tiers.ROLES[role][1]


def architect_prompt(mission: str) -> str:
    return f"{ARCHITECT_SYSTEM}\nMISSION:\n{mission}\n"
