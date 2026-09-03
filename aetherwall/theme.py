from __future__ import annotations

import colorsys
import io
import json
import subprocess
import threading
import time
from pathlib import Path
from urllib.parse import unquote, urlsplit

from PIL import Image

CACHE = Path.home() / ".cache" / "aetherwall"
STATE_FILE = CACHE / "wallpaper-state.json"
_lock = threading.Lock()
_wallpaper_path = ""
_last_signature = None
_last_video_sample = 0.0
_video_duration = None

DEFAULT_THEME = {
    "panel":"#e8070b17", "panelSolid":"#070b17", "text":"#f6f7ff", "muted":"#c0c8dc",
    "accent":"#b05cff", "accent2":"#22c8ff", "accent3":"#78ff35",
    "grid":"#559aa3bb", "track":"#cc252c42", "edge":"#30ffffff", "shadow":"#88000000",
}
_theme = {**DEFAULT_THEME, "zones": {}}


def _hex(rgb, alpha=None):
    r, g, b = [max(0, min(255, int(v))) for v in rgb]
    if alpha is None:
        return f"#{r:02x}{g:02x}{b:02x}"
    # Qt / QML requires #AARRGGBB format for 8-digit hex colors.
    a = max(0, min(255, int(alpha)))
    return f"#{a:02x}{r:02x}{g:02x}{b:02x}"


def _rel_luma(rgb):
    r, g, b = [v / 255.0 for v in rgb]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _zone_theme(rgb):
    r, g, b = rgb
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    lum = _rel_luma(rgb)
    # Local contrast: each HUD region gets its own glass/text treatment.
    bright = lum > 0.56
    # A complementary hue makes the accent separate from the local image.
    base_h = 0.73 if s < 0.10 else (h + 0.50) % 1.0
    # Avoid low-value accents that disappear into dark imagery.
    accent_v = 0.58 if bright else 1.0
    text = (16, 20, 32) if bright else (247, 249, 255)
    muted = (54, 64, 84) if bright else (201, 210, 229)
    panel = (248, 251, 255, 224) if bright else (5, 9, 20, 216)
    grid = (35, 44, 66, 72) if bright else (170, 180, 205, 62)
    track = (90, 99, 122, 105) if bright else (20, 27, 45, 220)
    edge = (255,255,255,115) if bright else (255,255,255,48)
    shadow = (0,0,0,115) if bright else (0,0,0,145)
    acc=[]
    for offset, sat in ((0.0,0.94),(0.14,0.90),(0.28,0.92)):
        rr,gg,bb=colorsys.hsv_to_rgb((base_h+offset)%1.0,sat,accent_v)
        acc.append((rr*255,gg*255,bb*255))
    return {
        "panel":_hex(panel[:3],panel[3]), "panelSolid":_hex(panel[:3]),
        "text":_hex(text), "muted":_hex(muted),
        "accent":_hex(acc[0]), "accent2":_hex(acc[1]), "accent3":_hex(acc[2]),
        "grid":_hex(grid[:3],grid[3]), "track":_hex(track[:3],track[3]),
        "edge":_hex(edge[:3],edge[3]), "shadow":_hex(shadow[:3],shadow[3]),
    }


def _average_region(image: Image.Image, box):
    w,h=image.size
    x0=max(0,min(w-1,int(box[0]*w))); y0=max(0,min(h-1,int(box[1]*h)))
    x1=max(x0+1,min(w,int(box[2]*w))); y1=max(y0+1,min(h,int(box[3]*h)))
    crop=image.crop((x0,y0,x1,y1)).convert("RGB")
    crop.thumbnail((64,64), Image.Resampling.BILINEAR)
    pixels=list(crop.getdata())
    if not pixels: return (128,128,128)
    # Downweight near-black/near-white pixels so bars/highlights don't dominate.
    total=[0.0,0.0,0.0]; tw=0.0
    for r,g,b in pixels:
        hh,ss,vv=colorsys.rgb_to_hsv(r/255,g/255,b/255)
        weight=0.7 + ss*1.8
        if vv < 0.04 or vv > 0.98: weight *= 0.45
        total[0]+=r*weight; total[1]+=g*weight; total[2]+=b*weight; tw+=weight
    return tuple(x/tw for x in total)


def _theme_for_image(image: Image.Image):
    # Regions correspond to the actual HUD geometry at the 1600x900 design grid.
    regions={
        "brand":(0.02,0.03,0.36,0.16),
        "left":(0.02,0.20,0.22,0.98),
        "clock":(0.73,0.04,0.98,0.23),
        "system":(0.72,0.26,0.98,0.58),
        "graph":(0.46,0.62,0.75,0.98),
    }
    zones={name:_zone_theme(_average_region(image,box)) for name,box in regions.items()}
    # Global fallback is a robust median-ish blend of the five zones.
    base=zones["system"]
    return {**base, "zones":zones}


def _load_image(path: Path):
    with Image.open(path) as image:
        return _theme_for_image(image.convert("RGB"))


def _video_duration_seconds(path: Path):
    try:
        out=subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(path)],text=True,stderr=subprocess.DEVNULL,timeout=5).strip()
        value=float(out); return value if value>0 else None
    except (OSError,ValueError,subprocess.SubprocessError): return None


def _load_video_theme(path: Path):
    global _video_duration
    if _video_duration is None: _video_duration=_video_duration_seconds(path)
    timestamp=1.0 if not _video_duration else time.monotonic()%max(1.0,_video_duration)
    try:
        raw=subprocess.check_output(["ffmpeg","-loglevel","error","-ss",f"{timestamp:.2f}","-i",str(path),"-frames:v","1","-vf","scale=640:-2","-f","image2pipe","-vcodec","png","pipe:1"],timeout=8)
        with Image.open(io.BytesIO(raw)) as image: return _theme_for_image(image.convert("RGB"))
    except (OSError,subprocess.SubprocessError,ValueError): return None


def _normalize_path(path: str):
    if not path: return ""
    try:
        parsed=urlsplit(path)
        if parsed.scheme=="file": return unquote(parsed.path)
    except ValueError: pass
    return str(Path(path).expanduser())


def set_wallpaper(path: str):
    global _wallpaper_path,_video_duration,_last_signature
    normalized=_normalize_path(path)
    with _lock:
        _wallpaper_path=normalized; _video_duration=None; _last_signature=None
    CACHE.mkdir(parents=True,exist_ok=True)
    tmp=STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps({"path":_wallpaper_path}),encoding="utf-8"); tmp.replace(STATE_FILE)


def requested_wallpaper(path: str):
    global _wallpaper_path,_video_duration,_last_signature
    normalized=_normalize_path(path)
    if normalized and normalized!=_wallpaper_path:
        with _lock:
            _wallpaper_path=normalized; _video_duration=None; _last_signature=None


def current_theme(force=False):
    global _theme, _last_signature, _last_video_sample
    with _lock:
        target_path = _wallpaper_path
        last_video = _last_video_sample
        last_sig = _last_signature
        cached_theme = dict(_theme)
    path = Path(target_path) if target_path else None
    if not path or not path.exists():
        return cached_theme
    suffix = path.suffix.lower()
    is_video = suffix in {".mp4", ".mkv", ".webm", ".mov", ".avi", ".m4v"}
    now = time.monotonic()
    try:
        if is_video:
            if not force and (now - last_video < 1.8):
                return cached_theme
            new_theme = _load_video_theme(path)
            sig = (str(path), round(now / 1.8))
        else:
            stat = path.stat()
            sig = (str(path), stat.st_mtime_ns, stat.st_size)
            if not force and sig == last_sig:
                return cached_theme
            new_theme = _load_image(path)
    except (OSError, ValueError):
        return cached_theme
    if new_theme is None:
        return cached_theme
    with _lock:
        _theme = new_theme
        _last_signature = sig
        if is_video:
            _last_video_sample = now
        return dict(_theme)
