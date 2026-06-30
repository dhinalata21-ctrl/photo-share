"""Build visual previews for folder confirmation."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path

from photoshare.server import list_photos, make_thumb

PREVIEW_LIMIT = 30


@dataclass
class FolderPreview:
    folder: Path
    photo_count: int
    sample_names: list[str]
    thumbnails_b64: list[str]
    total_size_mb: float


def folder_size_mb(folder: Path, photo_names: list[str]) -> float:
    total = 0
    for rel in photo_names[:200]:
        try:
            total += (folder / rel).stat().st_size
        except OSError:
            continue
    if len(photo_names) > 200 and photo_names:
        total = int(total * (len(photo_names) / min(len(photo_names), 200)))
    return round(total / (1024 * 1024), 1)


def build_folder_preview(folder: Path) -> FolderPreview:
    folder = folder.resolve()
    names = list_photos(folder)
    samples = names[:PREVIEW_LIMIT]
    thumbs: list[str] = []

    for rel in samples:
        source = folder / rel
        try:
            data = make_thumb(folder, rel, source)
            thumbs.append(base64.b64encode(data).decode("ascii"))
        except OSError:
            thumbs.append("")

    return FolderPreview(
        folder=folder,
        photo_count=len(names),
        sample_names=samples,
        thumbnails_b64=thumbs,
        total_size_mb=folder_size_mb(folder, names),
    )
