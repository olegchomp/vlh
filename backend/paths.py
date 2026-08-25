"""Resolve app paths for dev and PyInstaller frozen builds."""

from __future__ import annotations

import sys
from pathlib import Path


def resource_dir() -> Path:
    """Read-only bundled files (static HTML, seed JSON)."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def app_dir() -> Path:
    """Writable directory next to the exe (or project root in dev)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


STATIC_DIR = resource_dir() / "static"
DATA_DIR = app_dir() / "data"
SEED_STATE_PATH = resource_dir() / "data" / "state.json"
STATE_PATH = DATA_DIR / "state.json"
