#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "Installing Share Photos..."

if ! python3 -c "import tkinter" 2>/dev/null; then
  echo "tkinter is required for the app window."
  if command -v apt-get >/dev/null 2>&1; then
    echo "Installing python3-tk..."
    sudo apt-get install -y python3-tk
  else
    echo "Please install tkinter for Python 3, then run this script again."
    exit 1
  fi
fi

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
