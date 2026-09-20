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


def check_citations(report_path: str, sources_path: str) -> set:
    """Report URLs that do NOT appear in the explorer source corpus.

    P19a: citation verification is membership, not counting. A report fails
    its wave if ANY cited URL was never surfaced by an explorer output.
    Missing/unreadable files -> every report URL counts as unverified.
    """
    import re
    URL = re.compile(r"https?://[^\s)\]>\"']+")
    try:
        with open(report_path) as f:
            report_urls = set(URL.findall(f.read()))
    except OSError:
        return {"<unreadable report>"}
    try:
        with open(sources_path) as f:
            source_urls = set(URL.findall(f.read()))
    except OSError:
        source_urls = set()
    return report_urls - source_urls


_URL_RX = "https?://"
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def wave_cmds(report_path: str, sources_path: str | None = None) -> list:
    """F1: report exists and is non-empty.
    F2 (P19a real mode, sources_path given): >=3 URLs AND every report URL
    appears in the explorer corpus (membership, not URL-shape counting).
    F2 legacy mode (no sources_path): >=3 http(s) URLs inside the report.
    """
    f2 = (f"python3 -c \"import sys,re;t=open('{report_path}').read();"
          "sys.exit(0 if len(re.findall(r'https?://', t))>=3 else 1)\"")
    if sources_path:
        f2 = ("python3 -c \"import sys,re; "
              f"sys.path.insert(0, r'{_REPO_ROOT}'); "
              "from lib import research as r; "
              f"t=open(r'{report_path}').read(); "
              f"bad=r.check_citations(r'{report_path}', r'{sources_path}'); "
              f"n=len(re.findall(r'{_URL_RX}', t)); "
              "sys.exit(0 if (n>=3 and not bad) else 1)\"")
    return [
        f"test -s {report_path}",
        f2,
    ]
