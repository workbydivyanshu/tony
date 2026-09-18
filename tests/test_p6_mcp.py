"""P6 RED proof: MCP visibility + planner-awareness must exist."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib import mcp, roles

# Captured live 2026-09-18 from `opencode mcp list` (ANSI included, verbatim shape).
SAMPLE = (
    "\x1b[0m\n\u250c  MCP Servers\n\u2502\n"
    "\u25cf  \u2713 websearch \x1b[90mconnected\n"
    "\u2502      \x1b[90mhttps://mcp.exa.ai/mcp?tools=web_search_exa\n"
    "\u2502\n"
    "\u25cf  \u2713 context7 \x1b[90mconnected\n"
    "\u2502      \x1b[90mnpx -y @upstash/context7-mcp\n"
    "\u2502\n"
    "\u25cf  \u2713 grep_app \x1b[90mconnected\n"
    "\u2502      \x1b[90mhttps://mcp.grep.app\n"
    "\u2502\n"
    "\u25cf  \u2713 lsp \x1b[90mconnected\n"
    "\u2502      \x1b[90m/home/divyu/.local/bin/node /home/divyu/.cache/opencode/packages/oh-my-openagent@beta/node_modules/oh-my-openagent/packages/lsp-daemon/dist/cli.js mcp\n"
    "\u2502\n"
    "\u25cf  \u2713 playwright \x1b[90mconnected\n"
    "\u2502      \x1b[90mnpx -y @playwright/mcp@latest\n"
    "\u2502\n"
    "\u2514  5 server(s)\n"
)

def test_parse_mcp_list():
    servers = mcp.parse_list(SAMPLE)
    names = [s["name"] for s in servers]
    assert names == ["websearch", "context7", "grep_app", "lsp", "playwright"], names
    assert all(s["connected"] for s in servers), servers

def test_architect_prompt_names_mcp():
    prompt = roles.architect_prompt("dummy mission", ["context7", "playwright"])
    assert "context7" in prompt and "playwright" in prompt, prompt[:200]
