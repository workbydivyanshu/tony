"""packaging.py — systemd user-unit builder + install. Stdlib only.

`tony --install-daemon` writes ~/.config/systemd/user/tony-daemon.service and
enables it with `systemctl --user enable --now` (user-level, no sudo). The
unit runs `tony --daemon` and restarts on failure."""
import os
import subprocess


def unit_text(tony_path: str) -> str:
    return f"""[Unit]
Description=tony daemon (free-model-native agent CLI)

[Service]
ExecStart={tony_path} --daemon
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
"""


def install(run=subprocess.run) -> dict:
    """Write the user unit + enable. Returns {unit_path, enabled}."""
    tony_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tony")
    unit_dir = os.path.join(os.path.expanduser("~"), ".config", "systemd", "user")
    os.makedirs(unit_dir, exist_ok=True)
    unit_path = os.path.join(unit_dir, "tony-daemon.service")
    with open(unit_path, "w") as f:
        f.write(unit_text(tony_path))
    for cmd in (["systemctl", "--user", "daemon-reload"],
                ["systemctl", "--user", "enable", "--now", "tony-daemon.service"]):
        r = run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            return {"unit_path": unit_path, "enabled": False, "error": (r.stderr or r.stdout).strip()[-300:]}
    return {"unit_path": unit_path, "enabled": True}
