from __future__ import annotations
import importlib.util
import re
import shutil
import subprocess
import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent
REQ = APP_ROOT / "requirements.txt"

# requirements.txt contains both Python requirements and Arch runtime
# requirements. The latter are comments so pip ignores them.
DEFAULT_ARCH = [
    "python",
    "python-pip",
    "ffmpeg",
    "qt6-tools",
    "qt6-multimedia",
    "qt6-5compat",
    "qt6-multimedia-ffmpeg",
    "qt6-declarative",
    "gstreamer",
    "gst-plugins-base",
    "gst-plugins-good",
    "gst-libav",
]


def read_requirements():
    py = []
    arch = []
    if REQ.exists():
        for raw in REQ.read_text().splitlines():
            line = raw.strip()
            if line.startswith("# ARCH:"):
                pkg = line.removeprefix("# ARCH:").strip()
                if pkg:
                    arch.append(pkg)
            elif line and not line.startswith("#"):
                py.append(line)
    return py, arch or DEFAULT_ARCH


def missing_python(requirements):
    missing = []
    for req in requirements:
        name = re.split(r"[<>=!~]", req, maxsplit=1)[0].strip()
        # Map distribution names to import names where they differ.
        module = {"PySide6": "PySide6", "Pillow": "PIL", "psutil": "psutil"}.get(name, name)
        if importlib.util.find_spec(module) is None:
            missing.append(req)
    return missing


def missing_arch(packages):
    if not shutil.which("pacman"):
        return []
    return [
        pkg for pkg in packages
        if subprocess.run(
            ["pacman", "-Q", pkg],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
    ]


def ensure():
    py_reqs, arch_reqs = read_requirements()

    missing = missing_python(py_reqs)
    if missing:
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])

    missing_system = missing_arch(arch_reqs)
    if missing_system:
        subprocess.check_call(["sudo", "pacman", "-S", "--needed", *missing_system])


def main():
    ensure()
    from .main import main as gui_main
    raise SystemExit(gui_main())


if __name__ == "__main__":
    main()
