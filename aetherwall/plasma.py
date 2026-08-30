from pathlib import Path
import subprocess
import time
import json
from urllib.parse import quote

IMAGE_PLUGIN = "org.aetherwall.wallpaper"
VIDEO_PLUGIN = "org.aetherwall.video"
VIDEO_EXTS = {".mp4", ".mkv", ".webm", ".mov", ".avi", ".m4v"}


def _qdbus():
    for candidate in ("qdbus6", "qdbus", "/usr/lib/qt6/bin/qdbus6", "/usr/bin/qdbus6"):
        if Path(candidate).is_absolute():
            if Path(candidate).exists():
                return candidate
        else:
            try:
                if subprocess.run(["bash", "-lc", f"command -v {candidate}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
                    return candidate
            except OSError:
                pass
    return None


def _js(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value), ensure_ascii=False)


def _configure(plugin, path, settings, revision):
    q = _qdbus()
    if not q:
        raise RuntimeError("qdbus6 was not found. Install qt6-tools.")
    p = Path(path).expanduser().resolve()
    media_url = "file://" + quote(str(p), safe="/")
    overlay_url = ""
    overlay_b_url = ""
    from .config import TELEMETRY_URL
    reactive = bool(settings.get("reactive", True))
    telemetry_url = TELEMETRY_URL if reactive else ""
    blur_enabled = bool(settings.get("blur_enabled", True))
    blur_strength = int(settings.get("blur_strength", 65))
    show_title = bool(settings.get("show_title", True))
    show_clock = bool(settings.get("show_clock", True))
    show_system = bool(settings.get("show_system", True))
    show_meters = bool(settings.get("show_meters", True))
    show_history = bool(settings.get("show_history", True))
    show_dock = bool(settings.get("show_dock", True))
    script = f"""
var ds = desktops();
for (var i = 0; i < ds.length; ++i) {{
    var d = ds[i];
    if (d.screen < 0) continue;
    d.wallpaperPlugin = {_js(plugin)};
    d.currentConfigGroup = Array('Wallpaper', {_js(plugin)}, 'General');
    d.writeConfig('mediaPath', {_js(media_url)});
    d.writeConfig('overlayPath', {_js(overlay_url)});
    d.writeConfig('overlayPathB', {_js(overlay_b_url)});
    d.writeConfig('telemetryPath', {_js(telemetry_url)});
    d.writeConfig('fitMode', {_js(settings.get("fit", "fill"))});
    d.writeConfig('mode', {_js("video" if plugin == VIDEO_PLUGIN else "image")});
    d.writeConfig('reactiveEnabled', {_js(reactive)});
    d.writeConfig('blurEnabled', {_js(blur_enabled)});
    d.writeConfig('blurStrength', {_js(blur_strength)});
    d.writeConfig('showTitle', {_js(show_title)});
    d.writeConfig('showClock', {_js(show_clock)});
    d.writeConfig('showSystem', {_js(show_system)});
    d.writeConfig('showMeters', {_js(show_meters)});
    d.writeConfig('showHistory', {_js(show_history)});
    d.writeConfig('showDock', {_js(show_dock)});
    d.writeConfig('revision', {_js(revision)});
    d.reloadConfig();
}}
"""
    proc = subprocess.run([q, "org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell.evaluateScript", script], capture_output=True, text=True, timeout=15)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "PlasmaShell evaluateScript failed").strip())
    return plugin


def apply(path, settings):
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        raise RuntimeError(f"Wallpaper file does not exist: {p}")
    from .config import OVERLAY, OVERLAY_B
    mode = "video" if p.suffix.lower() in VIDEO_EXTS else "image"
    plugin = VIDEO_PLUGIN if mode == "video" else IMAGE_PLUGIN
    revision = time.time_ns()
    _configure(plugin, p, settings, revision)
    try:
        from .theme import set_wallpaper
        set_wallpaper(str(p))
    except Exception:
        pass
    return (
        "Wallpaper applied successfully.\n\n"
        f"Plugin: {plugin}\n"
        f"Type: {mode.upper()}\n"
        f"Reactive HUD: {'ON' if settings.get('reactive', True) else 'OFF'}\n"
        f"HUD blur: {'ON' if settings.get('blur_enabled', True) else 'OFF'} ({settings.get('blur_strength',65)}%)\n\n"
        "The selected media and reactive HUD are rendered by the same Plasma wallpaper plugin."
    )
