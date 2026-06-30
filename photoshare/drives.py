"""Find folders and removable drives that may contain photos."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".heic", ".tif", ".tiff", ".raw", ".cr2", ".nef", ".arw"}


@dataclass(frozen=True)
class PhotoSource:
    path: Path
    label: str
    removable: bool
    photo_count: int


def _count_images(folder: Path, limit: int = 5000) -> int:
    count = 0
    try:
        for root, dirs, files in os.walk(folder):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for name in files:
                if Path(name).suffix.lower() in IMAGE_EXT:
                    count += 1
                    if count >= limit:
                        return count
    except OSError:
        return 0
    return count


def _has_dcim(folder: Path) -> bool:
    dcim = folder / "DCIM"
    return dcim.is_dir()


def _mount_candidates() -> list[Path]:
    user = os.environ.get("USER") or os.environ.get("LOGNAME") or ""
    bases = [
        Path(f"/run/media/{user}"),
        Path(f"/media/{user}"),
        Path("/mnt"),
    ]
    found: list[Path] = []
    seen: set[Path] = set()
    for base in bases:
        if not base.is_dir():
            continue
        try:
            for child in sorted(base.iterdir()):
                if child.is_dir() and child not in seen:
                    seen.add(child)
                    found.append(child)
        except OSError:
            continue
    return found


def _lsblk_removable() -> dict[Path, str]:
    labels: dict[Path, str] = {}
    try:
        result = subprocess.run(
            ["lsblk", "-o", "RM,MOUNTPOINT,LABEL", "-n", "-r"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return labels

    for line in result.stdout.splitlines():
        parts = line.split(None, 2)
        if len(parts) < 2 or parts[0] != "1":
            continue
        mount = parts[1]
        label = parts[2] if len(parts) > 2 else ""
        if mount and mount != "":
            labels[Path(mount)] = label or Path(mount).name
    return labels


def find_photo_sources() -> list[PhotoSource]:
    removable_labels = _lsblk_removable()
    sources: list[PhotoSource] = []

    for mount in _mount_candidates():
        removable = mount in removable_labels
        label = removable_labels.get(mount, mount.name)
        if _has_dcim(mount):
            target = mount / "DCIM"
            tag = f"SD card · {label} (DCIM)"
        else:
            target = mount
            tag = f"{'SD card' if removable else 'Drive'} · {label}"

        count = _count_images(target)
        if count:
            sources.append(
                PhotoSource(
                    path=target,
                    label=tag,
                    removable=removable,
                    photo_count=count,
                )
            )

    return sorted(sources, key=lambda s: (not s.removable, -s.photo_count, s.label.lower()))


def is_image_file(name: str) -> bool:
    return Path(name).suffix.lower() in IMAGE_EXT
