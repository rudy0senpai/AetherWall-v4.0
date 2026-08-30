#!/usr/bin/env bash
set -euo pipefail
APP="$HOME/.local/share/aetherwall"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_DIR="$HOME/.config/systemd/user"
ICON_ROOT="$HOME/.local/share/icons/hicolor"

echo "Installing AetherWall v4.0.0..."
mkdir -p "$APP" "$SERVICE_DIR" "$HOME/.local/bin"
rm -rf "$APP/aetherwall" "$APP/plasma" "$APP/assets"
cp -a "$SRC/aetherwall" "$APP/"
cp -a "$SRC/plasma" "$APP/"
cp -a "$SRC/assets" "$APP/"
cp "$SRC/requirements.txt" "$SRC/README.md" "$SRC/uninstall.sh" "$APP/"

sudo pacman -S --needed --noconfirm python python-pip ffmpeg qt6-tools qt6-declarative qt6-multimedia qt6-multimedia-ffmpeg qt6-5compat gstreamer gst-plugins-base gst-plugins-good gst-libav
python -m venv --system-site-packages "$APP/.venv"
"$APP/.venv/bin/python" -m pip install --upgrade pip
"$APP/.venv/bin/python" -m pip install -r "$APP/requirements.txt"

mkdir -p "$HOME/.local/share/plasma/wallpapers" "$HOME/.local/share/plasma/plasmoids"
rm -rf "$HOME/.local/share/plasma/wallpapers/org.aetherwall.wallpaper" "$HOME/.local/share/plasma/wallpapers/org.aetherwall.video"
rm -rf "$HOME/.local/share/plasma/plasmoids/org.aetherwall.widget"
cp -a "$SRC/plasma/org.aetherwall.wallpaper" "$HOME/.local/share/plasma/wallpapers/"
cp -a "$SRC/plasma/org.aetherwall.video" "$HOME/.local/share/plasma/wallpapers/"
cp -a "$SRC/plasma/org.aetherwall.widget" "$HOME/.local/share/plasma/plasmoids/"

# Use the supplied AetherWall icon as the application icon at common sizes.
for size in 64 128 256 512; do
  mkdir -p "$ICON_ROOT/${size}x${size}/apps"
  cp "$SRC/assets/aetherwall.png" "$ICON_ROOT/${size}x${size}/apps/aetherwall.png"
done

mkdir -p "$HOME/.local/share/applications"
cat > "$HOME/.local/share/applications/aetherwall.desktop" <<EOF
[Desktop Entry]
Name=AetherWall
Comment=Reactive Plasma Wallpaper Engine
Exec=$HOME/.local/bin/aetherwall
Icon=aetherwall
Terminal=false
Type=Application
Categories=Utility;Graphics;
StartupWMClass=AetherWall
EOF

command -v kbuildsycoca6 >/dev/null 2>&1 && kbuildsycoca6 >/dev/null 2>&1 || true
command -v kpackagetool6 >/dev/null 2>&1 && kpackagetool6 --type Plasma/Applet --upgrade "$HOME/.local/share/plasma/plasmoids/org.aetherwall.widget" >/dev/null 2>&1 || true

cat > "$HOME/.local/bin/aetherwall" <<EOF
#!/usr/bin/env bash
cd "$APP"
exec "$APP/.venv/bin/python" -m aetherwall.bootstrap "\$@"
EOF
chmod +x "$HOME/.local/bin/aetherwall"
for shell_file in "$HOME/.bashrc" "$HOME/.profile"; do
  touch "$shell_file"
  grep -Fq 'export PATH="$HOME/.local/bin:$PATH"' "$shell_file" || printf '\n# AetherWall user launcher\nexport PATH="$HOME/.local/bin:$PATH"\n' >> "$shell_file"
done

cp "$SRC/aetherwall/aetherwall-telemetry.service" "$SERVICE_DIR/aetherwall-telemetry.service"
systemctl --user daemon-reload
systemctl --user enable aetherwall-telemetry.service
systemctl --user restart aetherwall-telemetry.service || systemctl --user start aetherwall-telemetry.service
rm -f "$HOME/.cache/aetherwall/reactive-overlay.png" "$HOME/.cache/aetherwall/reactive-overlay-b.png"

echo "AetherWall v4.0.0 installed."
echo "Application: $HOME/.local/share/applications/aetherwall.desktop"
echo "Image plugin: org.aetherwall.wallpaper"
echo "Video plugin: org.aetherwall.video"
echo "Widget: org.aetherwall.widget"
echo "Telemetry: http://127.0.0.1:8765/telemetry"
echo "Launcher: $HOME/.local/bin/aetherwall"
echo "Run: aetherwall"
