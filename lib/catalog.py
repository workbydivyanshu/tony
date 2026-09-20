"""catalog.py — live opencode free-model catalog reader. Stdlib only."""
import json
import os
import shutil
import subprocess
import time

HOME = os.path.expanduser("~")
TONY_DIR = os.path.join(HOME, ".tony")
CACHE_FILE = os.path.join(TONY_DIR, "catalog-cache.json")
CACHE_TTL = 60


def parse_models(raw: str) -> list:
    """Ground truth extractor: lines starting with opencode/. Never hardcode ids."""
    return sorted({line.strip() for line in raw.splitlines()
                   if line.strip().startswith("opencode/")})


def _cache_read() -> list | None:
    try:
        with open(CACHE_FILE) as f:
            data = json.load(f)
        if time.time() - data.get("ts", 0) < CACHE_TTL:
            return data.get("models", [])
    except (OSError, ValueError):
        pass
    return None


def _cache_write(models: list) -> None:
    try:
        os.makedirs(TONY_DIR, exist_ok=True)
        with open(CACHE_FILE, "w") as f:
            json.dump({"ts": time.time(), "models": models}, f)
    except OSError:
        pass


def resolve_bin(explicit: str | None = None) -> str:
    if explicit:
        return explicit
    env = os.environ.get("OPENCODE_BIN")
    if env:
        return env
    try:
        with open(os.path.join(TONY_DIR, "config.json")) as f:
            cfg = json.load(f)
        if cfg.get("opencode_bin"):
            return cfg["opencode_bin"]
    except (OSError, ValueError):
        pass
    return shutil.which("opencode") or "opencode"


def live_catalog(opencode_bin: str | None = None) -> list:
    """Read `opencode models`. Cached 60s. Fails loud, never silent."""
    bin = resolve_bin(opencode_bin)
    cached = _cache_read()
    if cached:
        return cached
    try:
        out = subprocess.run(
            [bin, "models"], capture_output=True, text=True, timeout=90
        ).stdout
    except (OSError, subprocess.TimeoutExpired) as e:
        raise RuntimeError(f"opencode models failed: {e}")
    models = parse_models(out)
    if not models:
        raise RuntimeError("opencode models returned zero opencode/* models")
    _cache_write(models)
    return models
