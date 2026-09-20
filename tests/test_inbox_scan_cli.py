"""tests/test_inbox_scan_cli.py — P31 deterministic --inbox-scan command.

Pins cmd_inbox_scan(scan_fn, notify_fn, outdir) with fakes only: report
content, exit codes, notify discipline (hits-only; quiet days stay quiet
per Hermes rule; infra failures never notify). Zero browser/HTTP.
"""
import glob
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib import inboxscan as tcli


def _outdir():
    import tempfile
    return tempfile.mkdtemp(prefix="tony-scan-cli-")


def test_quiet_day_report_no_notify():
    """575 rows, 0 hits -> exit 0, report with counts, notify silent."""
    import shutil
    outdir = _outdir()
    notified = []
    try:
        naved = []

        def scan_fn(session, keywords, max_pages):
            assert session == "tony-inbox-scan", session
            assert "interview" in keywords, keywords
            assert naved == [(session, "https://mail.proton.me/")], naved
            return {"pages": 12, "subjects": 575, "hits": []}
        code = tcli.run_scan(
            max_pages=12, scan_fn=scan_fn,
            nav_fn=lambda s, u: naved.append((s, u)),
            notify_fn=lambda t, b: notified.append((t, b)), outdir=outdir)
        assert code == 0, code
        assert notified == [], notified
        files = glob.glob(os.path.join(outdir, "*.md"))
        assert len(files) == 1, files
        body = open(files[0]).read()
        assert "575" in body and "12" in body, body
        assert "quiet" in body.lower(), body
    finally:
        shutil.rmtree(outdir, ignore_errors=True)


def test_hits_notify_and_report():
    """Keyword hit -> exit 0, notify once with sender/subject, in report."""
    import shutil
    outdir = _outdir()
    notified = []
    try:
        def scan_fn(session, keywords, max_pages):
            return {"pages": 12, "subjects": 575, "hits": [
                {"page": 4, "sender": "Acme Jobs",
                 "subject": "Interview invite: backend role"}]}
        code = tcli.run_scan(
            max_pages=12, scan_fn=scan_fn,
            nav_fn=lambda s, u: True,
            notify_fn=lambda t, b: notified.append((t, b)), outdir=outdir)
        assert code == 0, code
        assert len(notified) == 1, notified
        assert "Acme Jobs" in notified[0][1], notified
        assert "Interview invite" in notified[0][1], notified
        body = open(glob.glob(os.path.join(outdir, "*.md"))[0]).read()
        assert "Acme Jobs" in body and "Interview invite" in body, body
    finally:
        shutil.rmtree(outdir, ignore_errors=True)


def test_infra_failure_no_notify_exit_1():
    """Daemon down (scan raises) -> exit 1, failure on record, silent."""
    import shutil
    outdir = _outdir()
    notified = []
    try:
        def scan_fn(session, keywords, max_pages):
            raise ConnectionRefusedError("daemon down")
        code = tcli.run_scan(
            max_pages=12, scan_fn=scan_fn,
            nav_fn=lambda s, u: True,
            notify_fn=lambda t, b: notified.append((t, b)), outdir=outdir)
        assert code == 1, code
        assert notified == [], notified
        body = open(glob.glob(os.path.join(outdir, "*.md"))[0]).read()
        assert "ConnectionRefusedError" in body or "daemon" in body.lower(), body
    finally:
        shutil.rmtree(outdir, ignore_errors=True)


def test_login_wall_honest_verdict():
    """Pages read but zero rows -> 'login required' verdict, exit 0."""
    import shutil
    outdir = _outdir()
    notified = []
    try:
        def scan_fn(session, keywords, max_pages):
            return {"pages": 2, "subjects": 0, "hits": []}
        code = tcli.run_scan(
            max_pages=12, scan_fn=scan_fn,
            nav_fn=lambda s, u: True,
            notify_fn=lambda t, b: notified.append((t, b)), outdir=outdir)
        assert code == 0, code
        assert notified == [], notified
        body = open(glob.glob(os.path.join(outdir, "*.md"))[0]).read()
        assert "login" in body.lower(), body
    finally:
        shutil.rmtree(outdir, ignore_errors=True)


def test_navigates_to_inbox_first():
    """run_scan opens the inbox in a fresh tab before scanning."""
    import shutil
    outdir = _outdir()
    try:
        naved = []

        def nav_fn(session, url):
            naved.append((session, url))
            return True

        def scan_fn(session, keywords, max_pages):
            assert naved, "scan must run after navigate"
            return {"pages": 1, "subjects": 5, "hits": []}

        code = tcli.run_scan(
            max_pages=12, scan_fn=scan_fn, nav_fn=nav_fn,
            notify_fn=lambda t, b: None, outdir=outdir)
        assert code == 0, code
        assert len(naved) == 1, naved
        assert "mail.proton.me" in naved[0][1], naved
    finally:
        shutil.rmtree(outdir, ignore_errors=True)


def test_navigate_failure_is_infra():
    """Navigate raising -> exit 1, failure on record, silent notify."""
    import shutil
    outdir = _outdir()
    notified = []
    try:
        def nav_fn(session, url):
            raise ConnectionRefusedError("daemon down")

        def scan_fn(session, keywords, max_pages):
            raise AssertionError("scan must not run when navigate failed")

        code = tcli.run_scan(
            max_pages=12, scan_fn=scan_fn, nav_fn=nav_fn,
            notify_fn=lambda t, b: notified.append((t, b)), outdir=outdir)
        assert code == 1, code
        assert notified == [], notified
        body = open(glob.glob(os.path.join(outdir, "*.md"))[0]).read()
        assert "ConnectionRefusedError" in body or "navigate" in body.lower(), body
    finally:
        shutil.rmtree(outdir, ignore_errors=True)
