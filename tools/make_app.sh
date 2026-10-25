#!/bin/bash
# Builds "Social Empires.app" (double-click to play) for THIS copy of the project. macOS only.
# Re-run it if you move the project folder. Optional: ./tools/make_app.sh --install  (copies it to ~/Applications)
set -e
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
TMP="$(mktemp -d)"
sed "s|__PROJECT_DIR__|$ROOT|" tools/app/launcher.applescript > "$TMP/launcher.applescript"
rm -rf "Social Empires.app"
osacompile -s -o "Social Empires.app" "$TMP/launcher.applescript"
# icon from the project logo (optional, silently skipped if sips/iconutil fail)
(
  sips --padToHeightWidth 267 267 --padColor 669C2C templates/img/logo.png --out "$TMP/sq.png" >/dev/null
  mkdir "$TMP/i.iconset"
  for s in 16 32 128 256 512; do
    sips -z $s $s "$TMP/sq.png" --out "$TMP/i.iconset/icon_${s}x${s}.png" >/dev/null
    sips -z $((s*2)) $((s*2)) "$TMP/sq.png" --out "$TMP/i.iconset/icon_${s}x${s}@2x.png" >/dev/null
  done
  iconutil -c icns "$TMP/i.iconset" -o "$TMP/app.icns"
  cp "$TMP/app.icns" "Social Empires.app/Contents/Resources/applet.icns"
) >/dev/null 2>&1 || true
rm -rf "$TMP"
echo "Built: $ROOT/Social Empires.app"
if [ "$1" = "--install" ]; then
    mkdir -p ~/Applications && rm -rf ~/Applications/"Social Empires.app" && cp -R "Social Empires.app" ~/Applications/
    echo "Copied to ~/Applications"
fi
