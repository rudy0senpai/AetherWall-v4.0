#!/usr/bin/env bash
set -euo pipefail
systemctl --user disable --now aetherwall-telemetry.service >/dev/null 2>&1 || true
rm -f "$HOME/.config/systemd/user/aetherwall-telemetry.service"
systemctl --user daemon-reload >/dev/null 2>&1 || true
rm -f "$HOME/.cache/aetherwall/wallpaper-state.json"
rm -rf "$HOME/.local/share/plasma/wallpapers/org.aetherwall.wallpaper" "$HOME/.local/share/plasma/wallpapers/org.aetherwall.video" "$HOME/.local/share/plasma/plasmoids/org.aetherwall.widget" "$HOME/.local/share/aetherwall" "$HOME/.local/bin/aetherwall"
rm -f "$HOME/.local/share/applications/aetherwall.desktop"
for size in 64 128 256 512; do rm -f "$HOME/.local/share/icons/hicolor/${size}x${size}/apps/aetherwall.png"; done
command -v kbuildsycoca6 >/dev/null 2>&1 && kbuildsycoca6 >/dev/null 2>&1 || true
echo "AetherWall removed."
