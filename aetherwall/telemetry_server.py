from __future__ import annotations

import json
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

import psutil

from .theme import current_theme, requested_wallpaper, set_wallpaper
from .telemetry import cpu_average_temperature

HOST = "127.0.0.1"
PORT = 8765
HISTORY_SECONDS = 60

_lock = threading.Lock()
_latest = {
    "cpu": 0.0,
    "ram": 0.0,
    "ram_used": 0.0,
    "battery": 0.0,
    "power": "Unknown",
    "timestamp": 0.0,
    "history": [0.0] * HISTORY_SECONDS,
    "theme": current_theme(force=True),
}
_history = deque([0.0] * HISTORY_SECONDS, maxlen=HISTORY_SECONDS)


def read_metrics() -> dict:
    cpu = float(psutil.cpu_percent(interval=0.10))
    vm = psutil.virtual_memory()
    try:
        battery = psutil.sensors_battery()
    except (FileNotFoundError, OSError):
        battery = None
    batt = float(battery.percent) if battery else 0.0
    if battery is None:
        power = "Unknown"
    elif battery.power_plugged:
        power = "Charging"
    else:
        power = "On Battery"
    return {
        "cpu": cpu,
        "ram": float(vm.percent),
        "ram_used": vm.used / 1024**3,
        "battery": batt,
        "power": power,
        "cpu_temp": cpu_average_temperature(),
        "timestamp": time.time(),
    }


def update_metrics(metrics: dict, add_history: bool = False) -> None:
    global _latest
    with _lock:
        if add_history:
            _history.append(float(metrics["cpu"]))
        data = dict(metrics)
        data["history"] = list(_history)
        data["theme"] = current_theme()
        _latest = data


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlsplit(self.path)
        if parsed.path != "/telemetry":
            self.send_error(404)
            return

        params = parse_qs(parsed.query)
        media = params.get("media", [""])[0]
        if media:
            requested_wallpaper(media)

        with _lock:
            payload = json.dumps(_latest, separators=(",", ":")).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *_args):
        return


def main() -> None:
    psutil.cpu_percent(interval=None)
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    server.daemon_threads = True

    def updater():
        last_history = 0.0
        while True:
            started = time.monotonic()
            try:
                metrics = read_metrics()
                now = time.monotonic()
                add_history = now - last_history >= 1.0
                if add_history:
                    last_history = now
                update_metrics(metrics, add_history=add_history)
            except Exception as exc:
                print(f"AetherWall telemetry error: {exc}", flush=True)
            elapsed = time.monotonic() - started
            time.sleep(max(0.05, 0.25 - elapsed))

    # Restore the last selected media after service restart when available.
    try:
        from .theme import STATE_FILE
        if STATE_FILE.exists():
            state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            set_wallpaper(state.get("path", ""))
    except Exception:
        pass

    update_metrics(read_metrics(), add_history=True)
    threading.Thread(target=updater, name="aetherwall-telemetry", daemon=True).start()
    print(f"AetherWall telemetry server: http://{HOST}:{PORT}/telemetry", flush=True)
    server.serve_forever(poll_interval=0.25)


if __name__ == "__main__":
    main()
