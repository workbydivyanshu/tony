"""mcp.py — MCP visibility via opencode's own tool support. Stdlib only.

Tony NEVER talks MCP itself: `opencode run` role calls inherit the user's
opencode.json "mcp" servers + plugin lane automatically. This module only
reads `opencode mcp list` so the planner (architect prompt) and the operator
(--mcp-status / --status) can see what tools delegates already have.
"""
import re
import subprocess

ANSI = re.compile(r"\x1b\[[0-9;]*m")
_SERVER = re.compile(r"\u2713\s+(\S+)")


def parse_list(raw: str) -> list:
    """Parse `opencode mcp list` output -> [{name, connected}]."""
    text = ANSI.sub("", raw or "")
    servers = []
    for line in text.splitlines():
        m = _SERVER.search(line)
        if m:
            servers.append({"name": m.group(1),
                            "connected": "connected" in line})
    return servers


def live_servers(opencode_bin: str = "opencode",
                 timeout: int = 30) -> list:
    """Run `opencode mcp list` and parse. Empty list on any failure."""
    try:
        proc = subprocess.run([opencode_bin, "mcp", "list"],
                              capture_output=True, text=True,
                              timeout=timeout)
        if proc.returncode != 0:
            return []
        return parse_list((proc.stdout or "") + (proc.stderr or ""))
    except Exception:
        return []


def names(servers: list | None = None,
          opencode_bin: str = "opencode") -> list:
    """Server names, live by default; pass servers= to avoid a subprocess."""
    if servers is None:
        servers = live_servers(opencode_bin)
    return [s["name"] for s in servers if s.get("connected")]
