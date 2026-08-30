from pathlib import Path
import json
CONFIG_DIR=Path.home()/'.config'/'aetherwall'; CONFIG_FILE=CONFIG_DIR/'config.json'; CACHE=Path.home()/'.cache'/'aetherwall'; OVERLAY=CACHE/'reactive-overlay.png'; OVERLAY_B=CACHE/'reactive-overlay-b.png'; TELEMETRY=CACHE/'telemetry.json'; TELEMETRY_URL='http://127.0.0.1:8765/telemetry'
DEFAULT={'library':[],'favorites':[],'excluded':[],'wallpaper':'','reactive':True,'fit':'fill','fps':30,'hud3d':True,'blur_enabled':True,'blur_strength':65,'show_title':True,'show_clock':True,'show_system':True,'show_meters':True,'show_history':True,'show_dock':True,'rows':3}
def load():
    CONFIG_DIR.mkdir(parents=True,exist_ok=True); CACHE.mkdir(parents=True,exist_ok=True)
    try:d=json.loads(CONFIG_FILE.read_text()); x=DEFAULT.copy(); x.update(d); return x
    except Exception:return DEFAULT.copy()
def save(d):CONFIG_DIR.mkdir(parents=True,exist_ok=True); CONFIG_FILE.write_text(json.dumps(d,indent=2))
