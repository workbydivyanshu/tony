"""tests/test_packaging.py — P14 RED: systemd unit + notify hook must not exist."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_module_exists():
    from lib import packaging  # noqa: F401


def test_unit_text():
    from lib import packaging
    t = packaging.unit_text("/home/x/tony/tony")
    assert "ExecStart=/home/x/tony/tony --daemon" in t
    assert "[Unit]" in t and "[Install]" in t and "[Service]" in t
    assert "Restart=on-failure" in t
    assert "WantedBy=default.target" in t


def test_notify_hook():
    from lib import daemon
    calls = []
    daemon.notify("tony", "mission done", run=lambda c, **k: calls.append(c) or 0)
    assert calls and "notify-send" in calls[0] and "mission done" in calls[0]
