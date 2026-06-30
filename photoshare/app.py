"""Desktop app for sharing photos to a phone over Wi-Fi."""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from photoshare.drives import find_photo_sources
from photoshare.network import get_local_ip
from photoshare.server import PhotoServer, list_photos

DEFAULT_PORT = 8080


class PhotoShareApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Share Photos")
        self.root.minsize(520, 420)
        self.root.geometry("560x500")

        self.server = PhotoServer(Path.home(), port=DEFAULT_PORT)
        self.selected_dir: Path | None = None
        self.photo_count = 0

        self._build_ui()
        self.refresh_drives()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self) -> None:
        pad = {"padx": 16, "pady": 6}
        frame = ttk.Frame(self.root, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text="Share photos to your phone",
            font=("", 15, "bold"),
        ).pack(anchor=tk.W, pady=(0, 4))
        ttk.Label(
            frame,
            text="Pick a folder or SD card — no copying, no Telegram upload needed.",
            wraplength=500,
        ).pack(anchor=tk.W, pady=(0, 12))

        actions = ttk.Frame(frame)
        actions.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(actions, text="Choose folder…", command=self.choose_folder).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ttk.Button(actions, text="Refresh SD cards", command=self.refresh_drives).pack(
            side=tk.LEFT
        )

        ttk.Label(frame, text="SD cards & drives").pack(anchor=tk.W, **pad)
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        self.drive_list = tk.Listbox(list_frame, height=6, activestyle="dotbox")
        scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.drive_list.yview)
        self.drive_list.configure(yscrollcommand=scroll.set)
        self.drive_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.drive_list.bind("<Double-Button-1>", self._use_selected_drive)

        self.folder_label = ttk.Label(frame, text="No folder selected", wraplength=500)
        self.folder_label.pack(anchor=tk.W, **pad)

        self.status_label = ttk.Label(frame, text="Server stopped", foreground="#666")
        self.status_label.pack(anchor=tk.W, **pad)

        link_frame = ttk.LabelFrame(frame, text="Open this on your phone (same Wi-Fi)", padding=12)
        link_frame.pack(fill=tk.X, pady=(8, 0))
        self.link_var = tk.StringVar(value="Start sharing to get your link")
        link_entry = ttk.Entry(link_frame, textvariable=self.link_var, font=("", 12), state="readonly")
        link_entry.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(link_frame, text="Copy link", command=self.copy_link).pack(anchor=tk.W)

        btn_row = ttk.Frame(frame)
        btn_row.pack(fill=tk.X, pady=(12, 0))
        self.start_btn = ttk.Button(btn_row, text="Start sharing", command=self.start_sharing)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 8))
        self.stop_btn = ttk.Button(btn_row, text="Stop", command=self.stop_sharing, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT)

        self.sources: list[Path] = []

    def refresh_drives(self) -> None:
        self.drive_list.delete(0, tk.END)
        self.sources = []
        for source in find_photo_sources():
            self.sources.append(source.path)
            self.drive_list.insert(
                tk.END,
                f"{source.label}  —  {source.photo_count} photos",
            )
        if not self.sources:
            self.drive_list.insert(tk.END, "No SD cards detected — plug one in and click Refresh")

    def _use_selected_drive(self, _event=None) -> None:
        idxs = self.drive_list.curselection()
        if not idxs or idxs[0] >= len(self.sources):
            return
        self.set_folder(self.sources[idxs[0]])

    def choose_folder(self) -> None:
        folder = filedialog.askdirectory(title="Choose photo folder")
        if folder:
            self.set_folder(Path(folder))

    def set_folder(self, folder: Path) -> None:
        self.selected_dir = folder.resolve()
        self.folder_label.configure(text=str(self.selected_dir))
        threading.Thread(target=self._count_photos, daemon=True).start()

    def _count_photos(self) -> None:
        folder = self.selected_dir
        if not folder:
            return
        try:
            count = len(list_photos(folder))
        except OSError:
            count = 0

        def update() -> None:
            self.photo_count = count
            if folder == self.selected_dir:
                self.status_label.configure(
                    text=f"{count} photos ready" if count else "No photos found in this folder"
                )

        self.root.after(0, update)

    def start_sharing(self) -> None:
        if not self.selected_dir:
            messagebox.showinfo("Share Photos", "Choose a folder or SD card first.")
            return
        if self.photo_count == 0:
            messagebox.showwarning("Share Photos", "No photos found in that folder.")
            return

        self.server.stop()
        self.server = PhotoServer(self.selected_dir, port=DEFAULT_PORT)
        try:
            self.server.start()
        except OSError as exc:
            messagebox.showerror("Share Photos", f"Could not start server:\n{exc}")
            return

        ip = get_local_ip()
        link = f"http://{ip}:{DEFAULT_PORT}"
        self.link_var.set(link)
        self.status_label.configure(
            text=f"Sharing {self.photo_count} photos from {self.selected_dir.name}",
            foreground="#1a7f37",
        )
        self.start_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)

    def stop_sharing(self) -> None:
        self.server.stop()
        self.link_var.set("Start sharing to get your link")
        self.status_label.configure(text="Server stopped", foreground="#666")
        self.start_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)

    def copy_link(self) -> None:
        link = self.link_var.get()
        if not link.startswith("http"):
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(link)
        self.status_label.configure(text="Link copied — paste it in your phone browser", foreground="#1a7f37")

    def on_close(self) -> None:
        self.server.stop()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    try:
        root.iconname("Share Photos")
    except tk.TclError:
        pass
    PhotoShareApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
