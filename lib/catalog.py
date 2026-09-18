"""catalog.py — live opencode free-model catalog reader. Stdlib only."""
import json
import os
import subprocess
import time

HOME = os.path.expanduser("~")
TONY_DIR = os.path.join(HOME, ".tony")
CACHE_FILE = os.path.join(TONY_DIR, "catalog-cache.json")
CACHE_TTL = 60


def parse_models(raw: str) -> list:
    """Ground truth extractor: lines starting with opencode/. Never hardcode ids."""
    return sorted({l.strip() for l in raw.splitlines() if l.strip().startswith("opencode/")})


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


def live_catalog(opencode_bin: str = "opencode") -> list:
    """Read `opencode models`. Cached 60s. Fails loud, never silent."""
    cached = _cache_read()
    if cached:
        return cached
    try:
        out = subprocess.run(
            [opencode_bin, "models"], capture_output=True, text=True, timeout=90
        ).stdout
    except (OSError, subprocess.TimeoutExpired) as e:
        raise RuntimeError(f"opencode models failed: {e}")
    models = parse_models(out)
    if not models:
        raise RuntimeError("opencode models returned zero opencode/* models")
    _cache_write(models)
    return models
