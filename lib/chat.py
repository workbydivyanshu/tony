"""chat.py — conversational loop with persistent history (Hermes-replacement step 2). Stdlib only.

History: ~/.tony/chat/<session>.md, one exchange line each:
  - [YYYY-MM-DD HH:MM] user: text
  - [YYYY-MM-DD HH:MM] tony: text
"""
import os
import re
import time

SESSION_RE = re.compile(r"[^a-z0-9]+")
HISTORY_CAP = 20


def slugify_session(name: str) -> str:
    slug = SESSION_RE.sub("-", (name or "").lower()).strip("-")[:48]
    return slug or "default"


def chat_dir(home: str | None = None) -> str:
    base = home or os.path.expanduser("~")
    return os.path.join(base, ".tony", "chat")


def path_for(session: str, home: str | None = None) -> str:
    d = chat_dir(home)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, slugify_session(session) + ".md")


_LINE = re.compile(r"^-\s*\[[^\]]*\]\s*(user|tony)\s*:\s*(.*)$")


def append(session: str, role: str, text: str, home: str | None = None) -> str:
    """Append one exchange line. Returns the file path."""
    role = "user" if role == "user" else "tony"
    p = path_for(session, home)
    stamp = time.strftime("%Y-%m-%d %H:%M")
    with open(p, "a") as f:
        f.write(f"- [{stamp}] {role}: {(text or '').strip()}\n")
    return p


def load(session: str, home: str | None = None) -> list:
    """Parse history file into [{role, text}]. Missing file -> []."""
    import os as _os
    p = _os.path.join(chat_dir(home), slugify_session(session) + ".md")
    try:
        with open(p) as f:
            lines = f.readlines()
    except FileNotFoundError:
        return []
    out = []
    for ln in lines:
        m = _LINE.match(ln.strip())
        if m:
            out.append({"role": m.group(1), "text": m.group(2)})
    return out


def build_prompt(message: str, history: list | None = None,
                 memory_lines: list | None = None,
                 mcp_servers: list | None = None) -> str:
    """Assemble the conversational prompt: memory + recent history + current message."""
    parts = ["You are Tony, a concise helpful assistant. Reply directly, no preamble."]
    if memory_lines:
        parts.append("Persistent memory (respect these facts):\n" + "\n".join(memory_lines[-20:]))
    hist = list(history or [])[-HISTORY_CAP:]
    if hist:
        convo = "\n".join(f"{h['role']}: {h['text']}" for h in hist)
        parts.append("Conversation so far:\n" + convo)
    if mcp_servers:
        parts.append("Available MCP tools (via opencode): " + ", ".join(mcp_servers))
    parts.append("user: " + (message or "").strip())
    return "\n\n".join(parts) + "\n"


def repl(session: str, home: str | None = None, input_fn=None,
         output_fn=None, call_fn=None, prompt_builder=None) -> str:
    """Run the REPL until /quit or input exhaustion. Returns the session slug.

    prompt_builder(message, history) -> prompt; defaults to build_prompt
    with no memory/MCP. Live CLI passes one injecting fresh memory each turn
    so facts learned mid-chat apply immediately."""
    _in = input_fn or (lambda prompt: input(prompt))
    _out = output_fn or print
    if call_fn is None:
        raise ValueError("repl: call_fn required (live wiring passes engine.role_call)")
    _build = prompt_builder or (lambda msg, hist: build_prompt(msg, hist))
    slug = slugify_session(session)
    history = load(slug, home)
    while True:
        try:
            line = _in(f"{slug}> ")
        except (EOFError, StopIteration):
            break
        if line is None:
            break
        text = line.strip()
        if not text:
            continue
        if text == "/quit":
            break
        reply = call_fn(_build(text, history))
        _out(reply)
        append(slug, "user", text, home)
        append(slug, "tony", reply, home)
        history = history + [{"role": "user", "text": text},
                             {"role": "tony", "text": reply}]
    return slug
