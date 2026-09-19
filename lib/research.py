"""research.py — deep-research fan-out helpers. Stdlib only.

`tony research TOPIC` composes: 3 parallel explorer calls (distinct angles,
websearch MCP) -> researcher synthesis with cited sources -> critic gate ->
wave (report exists, >=3 http URLs). This module holds the pure prompt/wave
builders; orchestration lives in tony.cmd_research."""
import os
import re

ANGLES = (
    "current landscape: what exists today, who the main players/approaches are",
    "latest developments: news, releases, and changes from the last few months",
    "criticisms, risks, and open problems: what skeptics and users report",
)


def explorer_prompts(topic: str) -> list:
    """Three distinct explorer prompts. COST RULE (P16 probe: trivial calls
    answer in ~10s, tool-using missions take 60-125s+): start from local
    knowledge, use websearch MCP ONLY for facts that need the outside world
    (releases, news, current state). Parallel-safe."""
    return [
        (f"Answer from your own knowledge first. Use the websearch MCP tools "
         f"ONLY for facts you cannot know (recent releases, news, current "
         f"state). Angle: {angle}.\n"
         f"Topic: {topic}\n"
         "Return 4-6 bullet findings. EVERY bullet about an outside-world "
         "fact must end with the source URL it came from.")
        for angle in ANGLES
    ]


def synthesis_prompt(topic: str, findings: list) -> str:
    joined = "\n\n".join(f"--- explorer {i+1} ---\n{f}" for i, f in enumerate(findings))
    return (
        f"Synthesize a deep-research brief on: {topic}\n\n"
        f"{joined}\n\n"
        "Write the brief as markdown: 1-paragraph overview, then key findings "
        "grouped by theme, then an 'Open questions / risks' section. "
        "Cite every factual claim inline with its source URL. End with a "
        "'Sources' list of all URLs used. Do not invent URLs."
    )


def wave_cmds(report_path: str) -> list:
    """F1: report exists and is non-empty. F2: >=3 http(s) URLs inside."""
    f2 = (f"python3 -c \"import sys,re;t=open('{report_path}').read();"
          "sys.exit(0 if len(re.findall(r'https?://', t))>=3 else 1)\"")
    return [
        f"test -s {report_path}",
        f2,
    ]
