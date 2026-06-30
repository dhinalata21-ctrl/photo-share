#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "Installing Share Photos..."

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

.venv/bin/pip install -q -r requirements.txt

DESKTOP_DST="$HOME/Desktop/Share Photos.desktop"
sed "s|@PROJECT_DIR@|$PROJECT_DIR|g" "Share Photos.desktop" > "$DESKTOP_DST"
chmod +x "$PROJECT_DIR/launch.py"
chmod +x "$DESKTOP_DST"

if command -v gio >/dev/null 2>&1; then
  gio set "$DESKTOP_DST" metadata::trusted true 2>/dev/null || true
fi

echo ""
echo "Installed!"
echo "Double-click 'Share Photos' on your Desktop to launch."
