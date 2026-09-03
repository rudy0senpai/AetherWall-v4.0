from __future__ import annotations

from pathlib import Path
from datetime import datetime
import json
import os
import tempfile
import psutil
from collections import deque

CACHE = Path.home() / ".cache" / "aetherwall"
TELEMETRY_FILE = CACHE / "telemetry.json"
history = deque([0.0] * 60, maxlen=60)


def cpu_average_temperature() -> float | None:
    """Return average CPU/package-core temperature from available Linux sensors."""
    try:
        groups = psutil.sensors_temperatures(fahrenheit=False)
    except (AttributeError, FileNotFoundError, OSError):
        return None

    preferred = []
    fallback = []
    cpu_names = ("coretemp", "k10temp", "zenpower", "cpu", "processor", "x86_pkg_temp", "thinkpad", "soc_thermal", "cpu_thermal", "acpitz")
    non_cpu_names = ("nvme", "wifi", "wireless", "iwlwifi", "battery", "amdgpu", "nouveau")
    for name, entries in groups.items():
        lname = name.lower()
        if any(token in lname for token in non_cpu_names):
            continue
        target = preferred if any(token in lname for token in cpu_names) else fallback
        for entry in entries:
            current = getattr(entry, "current", None)
            try:
                value = float(current)
            except (TypeError, ValueError):
                continue
            if 0.0 < value < 125.0:
                target.append(value)

    readings = preferred or fallback
    return (sum(readings) / len(readings)) if readings else None


def sample():
    cpu = float(psutil.cpu_percent(interval=None))
    vm = psutil.virtual_memory()
    try:
        battery = psutil.sensors_battery()
    except (FileNotFoundError, OSError):
        battery = None
    batt = float(battery.percent) if battery else 0.0
    power = "Unknown" if battery is None else ("Charging" if battery.power_plugged else "On Battery")
    return {
        "cpu": cpu,
        "ram": float(vm.percent),
        "ram_used": vm.used / 1024**3,
        "battery": batt,
        "power": power,
        "cpu_temp": cpu_average_temperature(),
        "timestamp": datetime.now().isoformat(timespec="milliseconds"),
    }


def _atomic_json(data, target=TELEMETRY_FILE):
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".telemetry-", suffix=".json", dir=str(target.parent))
    os.close(fd)
    try:
        Path(tmp).write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
        os.replace(tmp, target)
    finally:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass


def publish(metrics):
    history.append(float(metrics["cpu"]))
    data = dict(metrics)
    data["history"] = list(history)
    _atomic_json(data)


def render(path=None, metrics=None, update_history=True):
    if metrics is None:
        metrics = sample()
    if update_history:
        publish(metrics)
