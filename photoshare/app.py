"""Modern desktop UI for Share Photos."""

from __future__ import annotations

import base64
import io
from pathlib import Path

import flet as ft
import qrcode

from photoshare.auth import generate_pin
from photoshare.drives import find_photo_sources
from photoshare.network import get_local_ip
from photoshare.preview import FolderPreview, build_folder_preview
from photoshare.server import PhotoServer

DEFAULT_PORT = 8080

BG = "#0c0f14"
SURFACE = "#161b22"
SURFACE_ALT = "#1f2630"
ACCENT = "#f0a830"
ACCENT_SOFT = "#f0a83033"
TEXT = "#f4f6f8"
TEXT_DIM = "#9aa4b2"
SUCCESS = "#3ecf8e"
BORDER = "#2a3340"


class SharePhotosApp:
    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.server = PhotoServer(Path.home(), port=DEFAULT_PORT)
        self.preview: FolderPreview | None = None
        self.share_link = ""
        self.pin_switch: ft.Switch | None = None
        self.pin_field: ft.TextField | None = None

        self.page.title = "Share Photos"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = BG
        self.page.padding = 0
        self.page.window.width = 960
        self.page.window.height = 720
        self.page.window.min_width = 760
        self.page.window.min_height = 600

        self.main = ft.Container(expand=True)
        self.page.add(self.main)
        self.show_home()

    def _set_view(self, content: ft.Control) -> None:
        self.main.content = ft.Container(
            content=content,
            expand=True,
            bgcolor=BG,
            padding=ft.Padding.symmetric(horizontal=28, vertical=24),
        )
        self.page.update()

    def _show_snack(self, message: str, bgcolor: str = SURFACE) -> None:
        self.page.show_dialog(ft.SnackBar(message, bgcolor=bgcolor))

    async def _browse_folder(self) -> None:
        path = await ft.FilePicker().get_directory_path(
            dialog_title="Choose your photo folder"
        )
        if path:
            self._pick_folder(Path(path))

    def show_home(self) -> None:
        self._set_view(self._build_home())

    def show_loading(self, label: str) -> None:
        self._set_view(
            ft.Column(
                [
                    ft.Container(expand=True),
                    ft.ProgressRing(color=ACCENT, width=56, height=56),
                    ft.Text(label, size=18, weight=ft.FontWeight.W_500, color=TEXT),
                    ft.Text("Building preview…", size=14, color=TEXT_DIM),
                    ft.Container(expand=True),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=16,
            )
        )

    def show_preview(self, preview: FolderPreview) -> None:
        self.preview = preview
        self._set_view(self._build_preview(preview))

    def show_sharing(self, public_link: str, qr_link: str, pin: str | None) -> None:
        self.share_link = public_link
        self._set_view(self._build_sharing(public_link, qr_link, pin))

    def _header(self, title: str, subtitle: str) -> ft.Column:
        return ft.Column(
            [
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Icon(ft.Icons.PHOTO_CAMERA_ROUNDED, color=BG, size=22),
                            bgcolor=ACCENT,
                            width=42,
                            height=42,
                            border_radius=12,
                            alignment=ft.Alignment.CENTER,
                        ),
                        ft.Column(
                            [
                                ft.Text(title, size=26, weight=ft.FontWeight.BOLD, color=TEXT),
                                ft.Text(subtitle, size=14, color=TEXT_DIM),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                    ],
                    spacing=14,
                ),
            ],
            spacing=8,
        )

    def _step_row(self, active: int) -> ft.Row:
        labels = ["Choose", "Preview", "Share"]
        items = []
        for i, label in enumerate(labels, start=1):
            done = i < active
            current = i == active
            dot_color = SUCCESS if done else (ACCENT if current else BORDER)
            text_color = TEXT if current else (SUCCESS if done else TEXT_DIM)
            items.append(
                ft.Row(
                    [
                        ft.Container(
                            width=28,
                            height=28,
                            border_radius=14,
                            bgcolor=dot_color if (done or current) else SURFACE,
                            border=ft.Border.all(2, dot_color),
                            alignment=ft.Alignment.CENTER,
                            content=ft.Icon(
                                ft.Icons.CHECK if done else None,
                                size=14,
                                color=BG if done else (BG if current else TEXT_DIM),
                            )
                            if done
                            else ft.Text(str(i), size=12, weight=ft.FontWeight.BOLD, color=BG if current else TEXT_DIM),
                        ),
                        ft.Text(label, size=13, color=text_color, weight=ft.FontWeight.W_600 if current else None),
                    ],
                    spacing=8,
                )
            )
            if i < len(labels):
                items.append(ft.Container(width=36, height=2, bgcolor=BORDER))
        return ft.Row(items, alignment=ft.MainAxisAlignment.CENTER)

    def _build_home(self) -> ft.Column:
        drives = find_photo_sources()
        drive_cards: list[ft.Control] = []

        for source in drives:
            icon = ft.Icons.SD_CARD if source.removable else ft.Icons.FOLDER_SPECIAL
            drive_cards.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Container(
                                content=ft.Icon(icon, color=ACCENT, size=30),
                                bgcolor=ACCENT_SOFT,
                                width=56,
                                height=56,
                                border_radius=14,
                                alignment=ft.Alignment.CENTER,
                            ),
                            ft.Column(
                                [
                                    ft.Text(source.label, size=16, weight=ft.FontWeight.W_600, color=TEXT),
                                    ft.Text(f"{source.photo_count} photos ready", size=13, color=TEXT_DIM),
                                    ft.Text(str(source.path), size=11, color=TEXT_DIM, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                ],
                                spacing=3,
                                expand=True,
                            ),
                            ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, size=16, color=TEXT_DIM),
                        ],
                        spacing=14,
                    ),
                    padding=18,
                    bgcolor=SURFACE,
                    border=ft.Border.all(1, BORDER),
                    border_radius=16,
                    ink=True,
                    on_click=lambda e, p=source.path: self._pick_folder(p),
                )
            )

        if not drive_cards:
            drive_cards.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.Icons.SD_CARD_ALERT, size=36, color=TEXT_DIM),
                            ft.Text("No SD card detected", size=15, weight=ft.FontWeight.W_500, color=TEXT),
                            ft.Text("Plug in your camera card and tap Refresh", size=13, color=TEXT_DIM),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    padding=28,
                    bgcolor=SURFACE,
                    border_radius=16,
                    border=ft.Border.all(1, BORDER),
                    alignment=ft.Alignment.CENTER,
                )
            )

        return ft.Column(
            [
                self._header("Share Photos", "Send shoots to your phone — no Telegram upload needed"),
                self._step_row(1),
                ft.Container(height=8),
                ft.Container(
                    content=ft.Row(
                        [
                            ft.ElevatedButton(
                                "Browse folder",
                                icon=ft.Icons.FOLDER_OPEN_ROUNDED,
                                bgcolor=ACCENT,
                                color=BG,
                                style=ft.ButtonStyle(
                                    padding=ft.Padding.symmetric(horizontal=22, vertical=16),
                                    shape=ft.RoundedRectangleBorder(radius=12),
                                ),
                                on_click=lambda _: self.page.run_task(self._browse_folder),
                            ),
                            ft.OutlinedButton(
                                "Refresh SD cards",
                                icon=ft.Icons.REFRESH,
                                style=ft.ButtonStyle(
                                    color=TEXT,
                                    padding=ft.Padding.symmetric(horizontal=18, vertical=16),
                                    shape=ft.RoundedRectangleBorder(radius=12),
                                ),
                                on_click=lambda _: self.show_home(),
                            ),
                        ],
                        spacing=12,
                    ),
                ),
                ft.Text("SD cards & drives", size=14, weight=ft.FontWeight.W_600, color=TEXT_DIM),
                ft.Column(drive_cards, spacing=10, scroll=ft.ScrollMode.AUTO, expand=True),
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.WIFI, size=16, color=TEXT_DIM),
                            ft.Text("Phone and computer must be on the same Wi-Fi", size=12, color=TEXT_DIM),
                        ],
                        spacing=8,
                    ),
                    padding=ft.Padding.only(top=8),
                ),
            ],
            spacing=14,
            expand=True,
        )

    def _build_preview(self, preview: FolderPreview) -> ft.Column:
        tiles: list[ft.Control] = []
        for idx, thumb in enumerate(preview.thumbnails_b64):
            if thumb:
                image = ft.Image(
                    src=f"data:image/jpeg;base64,{thumb}",
                    fit=ft.BoxFit.COVER,
                    gapless_playback=True,
                )
            else:
                image = ft.Icon(ft.Icons.BROKEN_IMAGE_OUTLINED, color=TEXT_DIM)
            name = preview.sample_names[idx].split("/")[-1]
            tiles.append(
                ft.Container(
                    content=ft.Stack(
                        [
                            ft.Container(
                                content=image,
                                expand=True,
                                bgcolor=SURFACE_ALT,
                            ),
                            ft.Container(
                                content=ft.Text(
                                    name,
                                    size=10,
                                    color=TEXT,
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                                bgcolor="#000000aa",
                                padding=ft.Padding.symmetric(horizontal=6, vertical=4),
                                bottom=0,
                                left=0,
                                right=0,
                            ),
                        ],
                        expand=True,
                    ),
                    border_radius=10,
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    aspect_ratio=1,
                    border=ft.Border.all(1, BORDER),
                )
            )

        extra = preview.photo_count - len(preview.sample_names)
        summary = (
            f"{preview.photo_count} photos  ·  ~{preview.total_size_mb} MB"
            if preview.total_size_mb
            else f"{preview.photo_count} photos"
        )

        return ft.Column(
            [
                self._header("Does this look right?", "Check the preview before sharing to your phone"),
                self._step_row(2),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(preview.folder.name, size=18, weight=ft.FontWeight.BOLD, color=TEXT),
                            ft.Text(str(preview.folder), size=12, color=TEXT_DIM),
                            ft.Text(summary, size=14, color=ACCENT, weight=ft.FontWeight.W_600),
                        ],
                        spacing=4,
                    ),
                    padding=16,
                    bgcolor=SURFACE,
                    border_radius=14,
                    border=ft.Border.all(1, BORDER),
                ),
                ft.Text(
                    f"Showing {len(tiles)} of {preview.photo_count}"
                    + (f"  (+{extra} more not shown)" if extra > 0 else ""),
                    size=13,
                    color=TEXT_DIM,
                ),
                ft.GridView(
                    controls=tiles,
                    expand=True,
                    max_extent=150,
                    child_aspect_ratio=1,
                    spacing=10,
                    run_spacing=10,
                ),
                self._build_pin_options(),
                ft.Row(
                    [
                        ft.OutlinedButton(
                            "Choose different folder",
                            icon=ft.Icons.ARROW_BACK,
                            style=ft.ButtonStyle(
                                color=TEXT,
                                padding=ft.Padding.symmetric(horizontal=18, vertical=16),
                                shape=ft.RoundedRectangleBorder(radius=12),
                            ),
                            on_click=lambda _: self.show_home(),
                        ),
                        ft.ElevatedButton(
                            "Yes — share these photos",
                            icon=ft.Icons.CHECK_CIRCLE,
                            bgcolor=SUCCESS,
                            color=BG,
                            style=ft.ButtonStyle(
                                padding=ft.Padding.symmetric(horizontal=22, vertical=16),
                                shape=ft.RoundedRectangleBorder(radius=12),
                            ),
                            on_click=lambda _: self._start_sharing(),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ],
            spacing=12,
            expand=True,
        )

    def _build_pin_options(self) -> ft.Container:
        self.pin_switch = ft.Switch(
            label="Protect pasted link with PIN",
            value=True,
            active_color=ACCENT,
            on_change=lambda _: self._update_pin_visibility(),
        )
        self.pin_field = ft.TextField(
            label="PIN or phrase",
            value=generate_pin(),
            password=True,
            can_reveal_password=True,
            width=360,
        )
        return ft.Container(
            content=ft.Column(
                [
                    self.pin_switch,
                    self.pin_field,
                    ft.Text(
                        "QR scan opens instantly. Anyone with the pasted link must enter this PIN.",
                        size=12,
                        color=TEXT_DIM,
                    ),
                ],
                spacing=10,
            ),
            padding=16,
            bgcolor=SURFACE,
            border_radius=14,
            border=ft.Border.all(1, BORDER),
        )

    def _update_pin_visibility(self) -> None:
        if self.pin_field and self.pin_switch:
            self.pin_field.visible = self.pin_switch.value
            self.page.update()

    def _qr_base64(self, url: str) -> str:
        qr = qrcode.QRCode(box_size=6, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#111111", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("ascii")

    def _build_sharing(self, public_link: str, qr_link: str, pin: str | None) -> ft.Column:
        qr_b64 = self._qr_base64(qr_link)
        count = self.preview.photo_count if self.preview else 0
        folder_name = self.preview.folder.name if self.preview else "photos"
        pin_row: list[ft.Control] = []
        if pin:
            pin_row = [
                ft.Container(height=6),
                ft.Row(
                    [
                        ft.Icon(ft.Icons.LOCK_OUTLINE, size=18, color=ACCENT),
                        ft.Text(
                            f"PIN for pasted link: {pin}",
                            size=15,
                            color=TEXT,
                            weight=ft.FontWeight.W_600,
                            selectable=True,
                        ),
                    ],
                    spacing=8,
                ),
                ft.Text(
                    "Share this PIN separately with anyone using the copied link.",
                    size=12,
                    color=TEXT_DIM,
                ),
            ]

        return ft.Column(
            [
                self._header("You're live!", "Scan QR for instant access — pasted links need PIN"),
                self._step_row(3),
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Container(
                                            content=ft.Row(
                                                [
                                                    ft.Container(width=10, height=10, bgcolor=SUCCESS, border_radius=5),
                                                    ft.Text("Sharing now", size=14, color=SUCCESS, weight=ft.FontWeight.W_600),
                                                ],
                                                spacing=8,
                                            ),
                                        ),
                                        ft.Text(folder_name, size=22, weight=ft.FontWeight.BOLD, color=TEXT),
                                        ft.Text(f"{count} photos available on your phone", size=14, color=TEXT_DIM),
                                        ft.Container(height=8),
                                        ft.Text("Pasted link", size=12, color=TEXT_DIM),
                                        ft.Text(public_link, size=17, color=ACCENT, weight=ft.FontWeight.W_600, selectable=True),
                                        *pin_row,
                                        ft.Container(height=8),
                                        ft.Row(
                                            [
                                                ft.ElevatedButton(
                                                    "Copy link",
                                                    icon=ft.Icons.CONTENT_COPY,
                                                    bgcolor=ACCENT,
                                                    color=BG,
                                                    on_click=lambda _: self._copy_link(public_link),
                                                ),
                                                ft.OutlinedButton(
                                                    "Stop sharing",
                                                    icon=ft.Icons.STOP_CIRCLE_OUTLINED,
                                                    style=ft.ButtonStyle(color=TEXT),
                                                    on_click=lambda _: self._stop_sharing(),
                                                ),
                                            ],
                                            spacing=10,
                                        ),
                                        ft.Text(
                                            "Same Wi-Fi → scan QR (no PIN) or paste link (PIN required)",
                                            size=12,
                                            color=TEXT_DIM,
                                        ),
                                    ],
                                    spacing=6,
                                ),
                                expand=True,
                                padding=20,
                            ),
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Image(src=f"data:image/png;base64,{qr_b64}", width=180, height=180),
                                        ft.Text("Scan QR — opens instantly", size=12, color=TEXT_DIM),
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    spacing=8,
                                ),
                                bgcolor="white",
                                border_radius=16,
                                padding=16,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        spacing=20,
                    ),
                    bgcolor=SURFACE,
                    border_radius=18,
                    border=ft.Border.all(1, BORDER),
                    padding=8,
                ),
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.PHOTO_LIBRARY_OUTLINED, color=ACCENT, size=20),
                            ft.Text(
                                "Scroll the album on your phone, tap to zoom, and save photos.",
                                size=13,
                                color=TEXT_DIM,
                                expand=True,
                            ),
                        ],
                        spacing=10,
                    ),
                    padding=ft.Padding.symmetric(horizontal=8),
                ),
                ft.OutlinedButton(
                    "Share a different folder",
                    icon=ft.Icons.FOLDER_OPEN,
                    style=ft.ButtonStyle(color=TEXT),
                    on_click=lambda _: self._stop_and_home(),
                ),
            ],
            spacing=14,
            expand=True,
        )

    def _pick_folder(self, folder: Path) -> None:
        self.show_loading(f"Loading {folder.name}…")

        def worker() -> None:
            try:
                preview = build_folder_preview(folder)
            except OSError as exc:

                async def show_error() -> None:
                    self._show_snack(f"Could not read folder: {exc}", "#5c1d1d")
                    self.show_home()

                self.page.run_task(show_error)
                return

            async def show_result() -> None:
                if preview.photo_count == 0:
                    self._show_snack("No photos found in that folder.", "#5c1d1d")
                    self.show_home()
                    return
                self.show_preview(preview)

            self.page.run_task(show_result)

        self.page.run_thread(worker)

    def _start_sharing(self) -> None:
        if not self.preview:
            return

        pin: str | None = None
        if self.pin_switch and self.pin_switch.value:
            pin = (self.pin_field.value if self.pin_field else "").strip()
            if not pin:
                self._show_snack("Enter a PIN or turn off link protection", "#5c1d1d")
                return

        self.server.stop()
        self.server = PhotoServer(self.preview.folder, port=DEFAULT_PORT, pin=pin)
        try:
            self.server.start()
        except OSError as exc:
            self._show_snack(f"Could not start: {exc}", "#5c1d1d")
            self.page.update()
            return
        ip = get_local_ip()
        public_link = f"http://{ip}:{DEFAULT_PORT}"
        qr_link = f"http://{ip}:{DEFAULT_PORT}{self.server.qr_path()}"
        self.show_sharing(public_link, qr_link, pin)

    def _stop_sharing(self) -> None:
        self.server.stop()
        self._show_snack("Sharing stopped")
        self.show_home()

    def _stop_and_home(self) -> None:
        self.server.stop()
        self.show_home()

    def _copy_link(self, link: str) -> None:
        self.page.set_clipboard(link)
        self._show_snack("Link copied!", SUCCESS)
        self.page.update()


def main() -> None:
    def run(page: ft.Page) -> None:
        app = SharePhotosApp(page)

        def on_close(e: ft.ControlEvent) -> None:
            app.server.stop()

        page.on_close = on_close

    ft.run(run)


if __name__ == "__main__":
    main()
