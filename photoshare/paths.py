"""Resolve bundled asset paths for dev and PyInstaller builds."""

from __future__ import annotations

import sys
from pathlib import Path


def package_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "photoshare"
    return Path(__file__).resolve().parent


def asset_path(name: str) -> Path:
    return package_dir() / name


def read_asset(name: str) -> str:
    return asset_path(name).read_text(encoding="utf-8")
