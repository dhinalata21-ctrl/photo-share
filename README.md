# Share Photos

Share hundreds of photos from your Linux PC (or directly from a camera SD card) to your phone over Wi-Fi — no Telegram upload, no copying files first.

Built for photographers on Lubuntu and other Linux desktops.

## What it does

1. **Double-click to launch** — modern step-by-step app (Choose → Preview → Share)
2. **Pick any folder or SD card** — auto-detects camera cards (`DCIM`)
3. **Visual preview** — see thumbnail grid before sharing so you know it's the right folder
4. **Share to phone** — QR code + link; scrollable album on her phone

Photos are served straight from the folder or SD card. Nothing is copied to your PC unless you choose a folder that's already on disk.

## Install

```bash
git clone https://github.com/dhinalata21-ctrl/photo-share.git
cd photo-share
./install.sh
```

Then double-click **Share Photos** on your Desktop.

### Manual run

```bash
./install.sh
cd photo-share
.venv/bin/python -m photoshare
```

## How to use (for your sister)

1. Double-click **Share Photos**
2. Plug in SD card **or** click **Browse folder**
3. **Check the preview grid** — make sure these are the photos she wants
4. Click **Yes — share these photos**
5. On her phone (same Wi-Fi), **scan the QR code** or tap **Copy link**
6. Scroll the album, tap photos to view, use **Save** to download
7. Click **Stop sharing** when done

## Why not Telegram?

Uploading 500+ full-size RAW/JPEG photos through Telegram on Linux often fails or is very slow. This shares files directly over your home Wi-Fi — faster and more reliable for large shoots.

## Requirements

- Python 3.10+
- Same Wi-Fi for phone and PC
- `install.sh` creates a virtual environment and installs dependencies (Flet, Pillow)

## SD card notes

- Insert the card before launching, or click **Refresh SD cards**
- The app looks in `/media` and `/run/media` for removable drives
- If the card has a `DCIM` folder (cameras), it shares from there automatically
- Thumbnails are cached in `~/.cache/photoshare/` — your SD card is never modified

## License

MIT
