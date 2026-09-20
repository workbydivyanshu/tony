"""TUI seam tests: stdlib curses TUI over existing renderer.

Fake-stdscr tests only — never require a real TTY. Plain-assert style
(pytest is broken in this env): stdout/TERM/curses patched manually
with save/restore, no fixtures.
"""
import sys
import os
import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib import tui, boulder


# ── Fake curses / fake stdscr ──────────────────────────────────────────────

class FakeWin:
    """Minimal curses window mock that records addstr calls and getch sequence."""
    def __init__(self, ch_sequence=None):
        self._ch_sequence = ch_sequence or []
        self._ch_idx = 0
        self.addstr_calls = []
        self.clear_calls = 0
        self.refresh_calls = 0
        self._keypad_set = None
        self._timeout_set = None

    def addstr(self, *args, **kwargs):
        self.addstr_calls.append((args, kwargs))

    def clear(self):
        self.clear_calls += 1

    def refresh(self):
        self.refresh_calls += 1

    def getch(self):
        if self._ch_idx < len(self._ch_sequence):
            ch = self._ch_sequence[self._ch_idx]
            self._ch_idx += 1
            return ch
        return -1  # no more input

    def keypad(self, val):
        self._keypad_set = val

    def timeout(self, val):
        self._timeout_set = val

    def nodelay(self, val):
        self._nodelay_set = val  # P19b: must NOT be called (100% CPU bug)
        raise AssertionError("nodelay() must not be used; use timeout()")

    def getmaxyx(self):
        return (24, 80)


def _make_curses_module(win):
    mod = types.ModuleType("curses")
    mod.initscr = lambda: win
    mod.curs_set = lambda *a, **k: None
    mod.noecho = lambda *a, **k: None
    mod.cbreak = lambda *a, **k: None
    mod.endwin = lambda *a, **k: None
    mod.error = Exception
    mod.KEY_UP = 259
    mod.KEY_DOWN = 258
    mod.KEY_RESIZE = 410
    return mod


_saved_curses = sys.modules.get("curses")


def _patch_curses(win):
    sys.modules["curses"] = _make_curses_module(win)


def _unpatch_curses():
    if _saved_curses is None:
        sys.modules.pop("curses", None)
    else:
        sys.modules["curses"] = _saved_curses


class _FakeStdout:
    def __init__(self, istty):
        self._istty = istty

    def isatty(self):
        return self._istty

    def write(self, s):
        pass

    def flush(self):
        pass


_real_stdout = sys.stdout
_real_term = os.environ.get("TERM")


def _set_tty(is_tty, term="xterm-256color"):
    sys.stdout = _FakeStdout(is_tty)
    os.environ["TERM"] = term


def _restore_tty():
    sys.stdout = _real_stdout
    if _real_term is None:
        os.environ.pop("TERM", None)
    else:
        os.environ["TERM"] = _real_term


# ── should_use_curses tests ────────────────────────────────────────────────

def test_should_use_curses_true():
    _set_tty(True)
    try:
        assert tui.should_use_curses() is True
    finally:
        _restore_tty()


def test_should_use_curses_false_no_tty():
    _set_tty(False)
    try:
        assert tui.should_use_curses() is False
    finally:
        _restore_tty()


def test_should_use_curses_false_dumb():
    _set_tty(True, term="dumb")
    try:
        assert tui.should_use_curses() is False
    finally:
        _restore_tty()


# ── run_tui: missing boulder returns 2 ─────────────────────────────────────

def test_run_tui_missing_boulder_returns_2():
    _set_tty(True)
    try:
        slug = "nonexistent-boulder-xyz"
        assert not os.path.exists(boulder.path_for(slug))
        assert tui.run_tui(slug, interval=0, timeout=0) == 2
    finally:
        _restore_tty()


# ── run_tui: fake-stdscr rendering + keymap ─────────────────────────────────

def _save_slug(slug, todos=("test todo",), wave=("test wave",)):
    b = boulder.new(slug)
    for t in todos:
        boulder.add_todo(b, t)
    for w in wave:
        boulder.add_wave(b, w)
    return boulder.save(slug, b)


def test_run_tui_snapshot_passes_to_window():
    _set_tty(True)
    bpath = _save_slug("tui-test-snap")
    win = FakeWin(ch_sequence=[ord("q")])
    _patch_curses(win)
    try:
        result = tui.run_tui("tui-test-snap", interval=0, timeout=0)
        all_text = " ".join(str(a) for (a, k) in win.addstr_calls)
        assert "TODOs:" in all_text, all_text[:200]
        assert "test todo" in all_text, all_text[:200]
        assert result == 0, result
    finally:
        _unpatch_curses()
        _restore_tty()
        os.unlink(bpath)


def test_run_tui_quit_key_returns_0():
    _set_tty(True)
    bpath = _save_slug("tui-test-quit", todos=("keep me open",), wave=())
    win = FakeWin(ch_sequence=[ord("q")])
    _patch_curses(win)
    try:
        assert tui.run_tui("tui-test-quit", interval=0, timeout=0) == 0
    finally:
        _unpatch_curses()
        _restore_tty()
        os.unlink(bpath)


def test_run_tui_force_refresh_key_r():
    _set_tty(True)
    bpath = _save_slug("tui-test-refresh", todos=("item 1",), wave=())
    win = FakeWin(ch_sequence=[ord("r"), ord("q")])
    _patch_curses(win)
    try:
        assert tui.run_tui("tui-test-refresh", interval=0, timeout=0) == 0
        assert len(win.addstr_calls) >= 2, len(win.addstr_calls)
    finally:
        _unpatch_curses()
        _restore_tty()
        os.unlink(bpath)


def test_run_tui_scroll_keys_j_k_up_down():
    _set_tty(True)
    bpath = _save_slug("tui-test-scroll", todos=("scroll item",), wave=())
    win = FakeWin(ch_sequence=[ord("j"), ord("k"), ord("q")])
    _patch_curses(win)
    try:
        assert tui.run_tui("tui-test-scroll", interval=0, timeout=0) == 0
        assert len(win.addstr_calls) >= 1
    finally:
        _unpatch_curses()
        _restore_tty()
        os.unlink(bpath)


def test_run_tui_timeout_returns_0():
    _set_tty(True)
    bpath = _save_slug("tui-test-timeout", todos=("never done",), wave=())
    win = FakeWin(ch_sequence=[-1])
    _patch_curses(win)
    try:
        assert tui.run_tui("tui-test-timeout", interval=0, timeout=1) == 0
    finally:
        _unpatch_curses()
        _restore_tty()
        os.unlink(bpath)


def test_run_tui_keypad_and_bounded_timeout():
    _set_tty(True)
    bpath = _save_slug("tui-test-config", todos=("config check",), wave=())
    win = FakeWin(ch_sequence=[ord("q")])
    _patch_curses(win)
    try:
        tui.run_tui("tui-test-config", interval=0, timeout=0)
        assert win._keypad_set is True
        # P19b: bounded getch wait instead of nodelay tight loop (100% CPU).
        assert win._timeout_set is not None and win._timeout_set >= 50, win._timeout_set
    finally:
        _unpatch_curses()
        _restore_tty()
        os.unlink(bpath)


def test_run_tui_curses_endwin_called():
    _set_tty(True)
    bpath = _save_slug("tui-test-endwin", todos=("endwin check",), wave=())
    ended = []
    win = FakeWin(ch_sequence=[ord("q")])
    _patch_curses(win)
    sys.modules["curses"].endwin = lambda *a, **k: ended.append(1)
    try:
        tui.run_tui("tui-test-endwin", interval=0, timeout=0)
        assert ended, "endwin must be called on exit"
    finally:
        _unpatch_curses()
        _restore_tty()
        os.unlink(bpath)


def test_run_tui_missing_boulder_after_load_returns_2():
    _set_tty(True)
    try:
        bpath = _save_slug("tui-test-deleted", todos=(), wave=())
        os.unlink(bpath)
        assert tui.run_tui("tui-test-deleted", interval=0, timeout=0) == 2
    finally:
        _restore_tty()


def test_run_tui_keyboard_interrupt_130():
    _set_tty(True)
    bpath = _save_slug("tui-test-kbi", todos=("kbi test",), wave=())

    class InterruptWin(FakeWin):
        def getch(self):
            raise KeyboardInterrupt

    _patch_curses(InterruptWin())
    try:
        assert tui.run_tui("tui-test-kbi", interval=0, timeout=0) == 130
    finally:
        _unpatch_curses()
        _restore_tty()
        os.unlink(bpath)


def test_run_tui_uses_existing_renderer():
    _set_tty(True)
    bpath = _save_slug("tui-test-reuse", todos=("reuse check",), wave=())
    win = FakeWin(ch_sequence=[ord("q")])
    _patch_curses(win)
    try:
        tui.run_tui("tui-test-reuse", interval=0, timeout=0)
        all_text = " ".join(str(a) for (a, k) in win.addstr_calls)
        assert "TODOs:" in all_text
        assert "reuse check" in all_text
    finally:
        _unpatch_curses()
        _restore_tty()
        os.unlink(bpath)
