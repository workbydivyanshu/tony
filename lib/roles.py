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
from inference — only from captured command output.

Never run git commit/push/add/reset — the operator owns all git writes."""


def role_model(role: str, assignments: dict) -> str:
    return assignments[role]


def role_effort(role: str) -> str:
    return tiers.ROLES[role][1]


CRITIC_SYSTEM = """You are the critic. Review completed work against the boulder plan.
Check that:
1. Every claimed file exists and is non-empty.
2. Wave commands match what was actually claimed done (no done-on-inference).
3. No TODO was marked done without captured command output proving it.

You MUST end your response with EXACTLY ONE of these lines (no other verdict format):
  VERDICT: PASS
  VERDICT: ISSUES

After the verdict line, list per-TODO evidence with lines like:
  EVIDENCE: TODO 1 <details>
  EVIDENCE: TODO 2 <details>
One line per TODO index. Do not omit evidence lines."""


def critic_prompt(boulder_markdown: str) -> str:
    """Build the critic prompt: rubric + boulder content."""
    return f"{CRITIC_SYSTEM}\nBOULDER:\n{boulder_markdown}\n"


def architect_prompt(mission: str, mcp_servers: list | None = None,
                     memory_lines: list | None = None,
                     matched_skills: list | None = None,
                     recon_lines: list | None = None,
                     workdir: str | None = None) -> str:
    # Enforcement boundary: prompts + plan gate. Sandboxing opencode out of scope.
    base = f"{ARCHITECT_SYSTEM}\nMISSION:\n{mission}\n"
    if workdir is not None:
        base += (f"\nTARGET DIRECTORY: {workdir} — all file writes, shell commands "
                 "and verification commands operate under this directory; "
                 "never write outside it.\n"
                 "Do not run git commit/push/add/reset; leave the tree uncommitted; "
                 "stay on the current branch unless the mission says otherwise.\n")
    if mcp_servers:
        base += ("\nAvailable MCP tools (via opencode, use them in TODOs where they fit): "
                 + ", ".join(mcp_servers) + "\n")
    if memory_lines:
        base += ("\nPersistent memory (facts from prior missions, respect them):\n"
                 + "\n".join(memory_lines[-20:]) + "\n")
    if recon_lines:
        base += ("\nRECON (explorer pass over the target repo — ground every "
                 "TODO in these findings, do not plan blind):\n"
                 + "\n".join(recon_lines) + "\n")
    from . import skills as skills_mod
    return skills_mod.inject_prompt(base, matched_skills or [])
