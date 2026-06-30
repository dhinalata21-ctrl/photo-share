# Share Photos

**Share hundreds of photos from Linux to your phone over Wi-Fi — no cloud upload, no Telegram struggle.**

A desktop app for photographers on **Lubuntu**, **Ubuntu**, and other Linux desktops. Pick a folder or plug in a camera SD card, preview your shots, and open a scrollable album on your phone in seconds.

---

## Who is this for?

- **Photographers** who shoot to SD card and want to review or send photos to a phone quickly
- **Anyone** tired of  failing on large Linux uploads (500+ full-size JPEGs/RAWs)
- **Linux users** who want a simple double-click app — not a terminal workflow

## The problem it solves

Uploading big photo batches through Telegram on Linux is often slow or fails entirely. **Share Photos** skips the upload step: your PC serves the files directly over your home Wi-Fi. Your phone browses a fast thumbnail gallery, taps to view full size, and saves what it needs.

**No copying to disk first** — serve straight from the SD card `DCIM` folder if you want.

---

## Features

| Feature | What it does |
|--------|----------------|
| **Double-click app** | Desktop launcher — no terminal needed after install |
| **SD card auto-detect** | Finds removable drives; opens `DCIM` when present |
| **Visual preview** | Thumbnail grid before sharing — confirm it's the right folder |
| **Phone album** | Scrollable grid, full-screen viewer, swipe, save to phone |
| **QR code** | Scan from your phone — instant access on same Wi-Fi |
| **Optional PIN** | Pasted links can require a PIN; QR scan skips PIN |
| **Lightweight** | Python + Flet UI; thumbnails cached locally |

---

## Quick start

```bash
git clone https://github.com/dhinalata21-ctrl/photo-share.git
cd photo-share
./install.sh
```

Then double-click **Share Photos** on your Desktop.

### Manual run

```bash
cd photo-share
.venv/bin/python -m photoshare
```

---

## How to use

1. Double-click **Share Photos**
2. Plug in an SD card **or** click **Browse folder**
3. Check the **preview grid** — make sure these are the right photos
4. *(Optional)* **Protect pasted link with PIN** — on by default; set a PIN or phrase
5. Click **Yes — share these photos**
6. On your phone (same Wi-Fi):
   - **Scan the QR code** → opens instantly
   - **Or paste the link** → enter PIN if protection is on
7. Scroll, tap to view, **Save** to download
8. Click **Stop sharing** when done

---

## Requirements

- Linux desktop (tested on Lubuntu)
- Python 3.10+
- Phone and PC on the **same Wi-Fi**
- `zenity` (installed automatically by `install.sh` on Debian/Ubuntu)

---

## Security & privacy

This app is designed for **trusted home Wi-Fi**, not the public internet.

- The server binds to your local network (`0.0.0.0:8080`) while sharing is active
- **PIN protection** is casual access control — deters casual link sharing, not nation-state attackers
- PINs are hashed (PBKDF2); unlock attempts are rate-limited (5 failures / 5 minutes per device)
- **QR links** contain a secret token and bypass PIN by design (for convenience when scanning in person)
- Traffic is **HTTP, not HTTPS** — use on private Wi-Fi you trust; stop sharing when finished
- Thumbnails cache in `~/.cache/photoshare/`; your photo folder/SD card is **never modified**

---

## SD card notes

- Insert the card before launching, or click **Refresh SD cards**
- Looks in `/media` and `/run/media` for removable drives
- If the card has `DCIM`, shares from there automatically

---

##  | Works offline on LAN |

---

## License

MIT — use freely, modify, share.

**Repo:** https://github.com/dhinalata21-ctrl/photo-share
