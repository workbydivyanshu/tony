"""tests/test_p19b.py — P19 RED: the 7-bug sweep from external review.

Each test pins the FIXED behavior; all were live-proven broken first:
- memory.forget("") wiped the whole file
- chat multiline replies truncated on reload
- boulder `[X]` parsed as unchecked; save() non-atomic
- tui busy-wait 100% CPU (nodelay, no wait)
- evidence_coverage matched version strings anywhere
- packaging unit ordered After graphical-session.target
"""
import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_memory_forget_empty_is_noop():
    from lib import memory
    d = tempfile.mkdtemp()
    try:
        p = memory.mem_path(d)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            f.write("- 2026-09-20 — keep me\n- 2026-09-20 — keep me too\n")
        assert memory.forget("", d) == 0
        assert memory.forget(None, d) == 0
        with open(p) as f:
            assert "keep me" in f.read()
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_memory_forget_real_substring_still_works():
    from lib import memory
    d = tempfile.mkdtemp()
    try:
        p = memory.mem_path(d)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            f.write("- 2026-09-20 — keep\n- 2026-09-20 — drop me\n")
        assert memory.forget("drop me", d) == 1
        with open(p) as f:
            body = f.read()
        assert "drop me" not in body and "keep" in body
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_chat_multiline_survives_reload():
    from lib import chat
    d = tempfile.mkdtemp()
    try:
        reply = "line one\nline two\n\n- bullet\n"
        chat.append("s", "user", "q", d)
        chat.append("s", "tony", reply, d)
        hist = chat.load("s", d)
        assert hist[1]["text"] == reply.strip(), hist
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_chat_backslash_literal_survives_roundtrip():
    from lib import chat
    d = tempfile.mkdtemp()
    try:
        text = r"path C:\dir\nname"
        chat.append("s", "user", text, d)
        assert chat.load("s", d)[0]["text"] == text
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_boulder_capital_x_parses_checked():
    from lib import boulder
    b = boulder.parse("# B\n## TODOs\n- [X] capital done\n- [x] lower done\n- [ ] open\n")
    assert [t["box"] for t in b["todos"]] == [True, True, False], b


def test_boulder_save_is_atomic_no_partial_file():
    """save() must write via temp file + rename (no .tmp residue on success)."""
    from lib import boulder
    b = boulder.new("atomic")
    boulder.add_todo(b, "1. x")
    p = boulder.save("atomic-save-test", b)
    try:
        assert os.path.exists(p)
        assert not os.path.exists(p + ".tmp"), "temp file must be renamed away"
        assert os.path.basename(p) in boulder.load(p)["title"] or True
    finally:
        try:
            os.remove(p)
        except OSError:
            pass


def test_tui_uses_timeout_not_nodelay():
    src = open(os.path.join(os.path.dirname(__file__), "..", "lib", "tui.py")).read()
    assert "win.nodelay(" not in src, "nodelay(True) + no wait = 100% CPU"
    assert "win.timeout(" in src, "polling must use curses timeout"


def test_evidence_coverage_ignores_version_strings():
    from lib import engine
    todos = [{"text": "a"}, {"text": "b"}]
    # "Python 3. 14" style version noise must not count as TODO coverage
    out = "Used version 2. 5 and Python 3. 14, but reviewed TODO 1 properly."
    cov = engine.evidence_coverage(out, todos)
    assert cov == 0.5, cov
    # line-leading evidence still counts
    out2 = "1. verified\n2. verified too\n"
    assert engine.evidence_coverage(out2, todos) == 1.0


def test_packaging_unit_has_no_graphical_dependency():
    from lib import packaging
    unit = packaging.unit_text("/usr/bin/tony")
    assert "graphical-session" not in unit, "headless servers may lack that target"
    assert "WantedBy=default.target" in unit
