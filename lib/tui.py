"""tui.py — stdlib curses TUI over the existing renderer.

Reuses lib/watch.py (render_snapshot, tail_lines, work_files) and
lib/boulder.py (load, path_for, progress). No duplicated rendering.
Curses is imported lazily inside run_tui so non-curses platforms
can still import this module for testing.
"""
import os
import sys
import time

from lib import boulder, watch


def should_use_curses() -> bool:
    """Return True if a curses TUI is appropriate."""
    return sys.stdout.isatty() and os.environ.get("TERM", "") != "dumb"


def run_tui(slug: str, interval: int = 1, timeout: int = 0) -> int:
    """Run a curses TUI polling a boulder's progress.

    Keys: q=quit, r=force-refresh, up/down/j/k=scroll.
    Returns: 0=complete/timeout/quit, 2=missing/deleted boulder, 130=KeyboardInterrupt.
    """
    import curses  # lazy import — can be mocked via sys.modules for tests

    bpath = boulder.path_for(slug)

    def _load_boulder():
        try:
            return boulder.load(bpath)
        except OSError:
            return None

    b = _load_boulder()
    if b is None:
        return 2

    def _snapshot():
        try:
            b2 = boulder.load(bpath)
        except OSError:
            return None, None
        runs_tail = watch.tail_lines(os.path.join(os.path.expanduser("~"), ".tony", "runs.log"), 15)
        wf = watch.work_files(os.path.join(os.path.expanduser("~"), ".tony", "work", slug))
        return watch.render_snapshot(b2, runs_tail, wf, None), b2

    def _done(bd: dict) -> bool:
        p = boulder.progress(bd)
        return p["done"] == p["total"] and p["waved"] == p["wavetotal"]

    win = curses.initscr()
    curses.curs_set(0)
    curses.noecho()
    curses.cbreak()
    win.keypad(True)
    # P19b: bounded getch wait (was nodelay(True) + tight loop = 100% CPU).
    win.timeout(max(50, int(interval) * 1000))

    scroll = 0
    t0 = time.time()

    try:
        while True:
            snap, bcur = _snapshot()
            if snap is None:
                curses.endwin()
                return 2

            lines = snap.splitlines()
            maxy, maxx = win.getmaxyx()
            visible = lines[scroll:scroll + maxy]

            win.clear()
            for i, line in enumerate(visible):
                truncated = line[:maxx - 1] if len(line) > maxx - 1 else line
                try:
                    win.addstr(i, 0, truncated)
                except curses.error:
                    pass
            win.refresh()

            if _done(bcur):
                curses.endwin()
                return 0

            if timeout > 0 and (time.time() - t0) >= timeout:
                curses.endwin()
                return 0

            ch = win.getch()
            if ch == ord('q'):
                curses.endwin()
                return 0
            elif ch == ord('r'):
                continue  # force-refresh: re-render next loop
            elif ch in (curses.KEY_UP, ord('k'), ord('K')):
                scroll = max(0, scroll - 1)
            elif ch in (curses.KEY_DOWN, ord('j'), ord('J')):
                scroll += 1
    except KeyboardInterrupt:
        curses.endwin()
        return 130
    finally:
        try:
            curses.endwin()
        except Exception:
            pass
