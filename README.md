# Share Photos

Share hundreds of photos from your Linux PC (or directly from a camera SD card) to your phone over Wi-Fi — no Telegram upload, no copying files first.

Built for photographers on Lubuntu and other Linux desktops.

## What it does

1. **Double-click to launch** — simple desktop app
2. **Pick any folder** — or auto-detect an inserted SD card (reads `DCIM` directly)
3. **Start sharing** — get a link like `http://192.168.1.50:8080`
4. **Open on your phone** — scrollable photo album, tap to view full size, save to phone

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
pip install --user -r requirements.txt
python3 -m photoshare
```

## How to use (for your sister)

1. Plug in the SD card **or** click **Choose folder**
2. If the SD card shows in the list, double-click it (opens `DCIM` automatically)
3. Click **Start sharing**
4. On your phone (same Wi-Fi), open the link shown — or tap **Copy link** and paste in Chrome/Safari
5. Scroll the album, tap photos to view, use **Save** to download
6. Click **Stop** when done

## Why not Telegram?

Uploading 500+ full-size RAW/JPEG photos through Telegram on Linux often fails or is very slow. This shares files directly over your home Wi-Fi — faster and more reliable for large shoots.

## Requirements

- Python 3.10+ with tkinter (`python3-tk` on Ubuntu/Lubuntu)
- Same Wi-Fi for phone and PC
- `install.sh` creates a local virtual environment and installs Pillow automatically

## SD card notes

- Insert the card before launching, or click **Refresh SD cards**
- The app looks in `/media` and `/run/media` for removable drives
- If the card has a `DCIM` folder (cameras), it shares from there automatically
- Thumbnails are cached in `~/.cache/photoshare/` — your SD card is never modified

## License

MIT
