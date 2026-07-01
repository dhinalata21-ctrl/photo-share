#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi

.venv/bin/pip install -q -r requirements.txt flet-cli pyinstaller

rm -rf dist build *.spec
.venv/bin/flet pack launch.py \
  --name SharePhotos \
  --product-name "Share Photos" \
  --product-version "${1:-1.0.0}" \
  --add-data "photoshare/gallery.html:photoshare" \
  --add-data "photoshare/pin.html:photoshare"

cp dist/SharePhotos "dist/SharePhotos-linux-x64"
chmod +x dist/SharePhotos-linux-x64

echo ""
echo "Built: dist/SharePhotos-linux-x64"
ls -lh dist/SharePhotos-linux-x64
