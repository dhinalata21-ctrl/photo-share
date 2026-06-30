"""HTTP gallery server for sharing photos over the local network."""

from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import threading
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
from urllib.parse import unquote

from PIL import Image

from photoshare.drives import is_image_file

THUMB_SIZE = 280
CACHE_DIR = Path.home() / ".cache" / "photoshare" / "thumbs"
GALLERY_HTML = (Path(__file__).parent / "gallery.html").read_text(encoding="utf-8")


class PhotoServer:
    def __init__(self, photo_dir: Path, port: int = 8080) -> None:
        self.photo_dir = photo_dir.resolve()
        self.port = port
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return self._server is not None

    def start(self) -> None:
        if self.running:
            return
        handler = self._make_handler()
        self._server = ThreadingHTTPServer(("0.0.0.0", self.port), handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if not self._server:
            return
        self._server.shutdown()
        self._server.server_close()
        self._server = None
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None

    def _make_handler(self):
        photo_dir = self.photo_dir

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, fmt, *args):
                pass

            def send_bytes(self, data: bytes, content_type: str, cache_seconds: int = 0):
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(data)))
                if cache_seconds:
                    self.send_header("Cache-Control", f"public, max-age={cache_seconds}")
                self.end_headers()
                self.wfile.write(data)

            def send_json(self, data, status=200):
                body = json.dumps(data).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(body)

            def send_file(self, path: Path, cache_seconds: int = 86400):
                if not path.is_file():
                    self.send_error(404)
                    return
                mime, _ = mimetypes.guess_type(str(path))
                mime = mime or "application/octet-stream"
                with path.open("rb") as handle:
                    data = handle.read()
                self.send_bytes(data, mime, cache_seconds)

            def resolve_rel(self, rel_path: str) -> Path | None:
                rel_path = rel_path.lstrip("/")
                target = (photo_dir / rel_path).resolve()
                if not str(target).startswith(str(photo_dir)):
                    return None
                return target

            def do_GET(self):
                path = unquote(self.path.split("?", 1)[0])

                if path in ("/", "/index.html"):
                    self.send_bytes(GALLERY_HTML.encode(), "text/html; charset=utf-8")
                    return

                if path == "/api/photos":
                    self.send_json(list_photos(photo_dir))
                    return

                if path.startswith("/thumb/"):
                    rel = path[len("/thumb/") :]
                    file_path = self.resolve_rel(rel)
                    if not file_path or not file_path.is_file():
                        self.send_error(404)
                        return
                    try:
                        data = make_thumb(photo_dir, rel, file_path)
                    except OSError:
                        self.send_error(404)
                        return
                    self.send_bytes(data, "image/jpeg", cache_seconds=604800)
                    return

                if path.startswith("/photos/"):
                    rel = path[len("/photos/") :]
                    file_path = self.resolve_rel(rel)
                    if not file_path:
                        self.send_error(403)
                        return
                    self.send_file(file_path)
                    return

                self.send_error(404)

        return Handler


def list_photos(photo_dir: Path) -> list[str]:
    names: list[str] = []
    for root, dirs, files in os.walk(photo_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for name in files:
            if is_image_file(name):
                rel = Path(root, name).relative_to(photo_dir).as_posix()
                names.append(rel)
    return sorted(names, key=str.lower)


@lru_cache(maxsize=4096)
def thumb_cache_key(photo_dir: str, rel_name: str, mtime_ns: int) -> str:
    return f"{photo_dir}:{rel_name}:{mtime_ns}:{THUMB_SIZE}"


def thumb_cache_path(photo_dir: Path, rel_name: str) -> Path:
    digest = hashlib.sha256(f"{photo_dir}:{rel_name}".encode()).hexdigest()[:40]
    return CACHE_DIR / f"{digest}.jpg"


def make_thumb(photo_dir: Path, rel_name: str, source: Path) -> bytes:
    thumb_cache_key(str(photo_dir), rel_name, source.stat().st_mtime_ns)
    cache_path = thumb_cache_path(photo_dir, rel_name)

    if cache_path.is_file() and cache_path.stat().st_mtime >= source.stat().st_mtime:
        return cache_path.read_bytes()

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as im:
        im = im.convert("RGB")
        im.thumbnail((THUMB_SIZE, THUMB_SIZE), Image.Resampling.LANCZOS)
        buf = BytesIO()
        im.save(buf, format="JPEG", quality=82, optimize=True)
        data = buf.getvalue()

    cache_path.write_bytes(data)
    return data
