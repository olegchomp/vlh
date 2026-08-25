"""VLH desktop entry: tray icon + background HTTP server (no console)."""

from __future__ import annotations

import os
import socket
import sys
import threading
import time
import traceback
import webbrowser
from multiprocessing import freeze_support

# Windowed PyInstaller sets stdout/stderr to None — uvicorn logging needs streams.
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

import pystray
import uvicorn
from PIL import Image, ImageDraw, ImageFont

from backend.main import app
from backend.paths import app_dir

HOST = "127.0.0.1"
PORT = 8765
URL = f"http://{HOST}:{PORT}/"

_server: uvicorn.Server | None = None
_icon: pystray.Icon | None = None


def _log_crash(exc: BaseException | None = None) -> None:
    try:
        path = app_dir() / "vlh-crash.log"
        text = traceback.format_exc() if exc is None else "".join(
            traceback.format_exception(type(exc), exc, exc.__traceback__)
        )
        path.write_text(text or "unknown error\n", encoding="utf-8")
    except Exception:
        pass


def _port_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False


def _wait_ready(timeout: float = 20.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((HOST, PORT), timeout=0.4):
                return True
        except OSError:
            time.sleep(0.2)
    return False


def _open_ui(icon=None, item=None) -> None:
    webbrowser.open(URL)


def _make_tray_image() -> Image.Image:
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((2, 2, size - 3, size - 3), radius=12, fill=(74, 122, 152, 255))
    try:
        font = ImageFont.truetype("segoeui.ttf", 18)
    except OSError:
        font = ImageFont.load_default()
    text = "VLH"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size - tw) / 2, (size - th) / 2 - 1), text, fill=(255, 255, 255, 255), font=font)
    return img


def _run_server() -> None:
    global _server
    try:
        config = uvicorn.Config(
            app,
            host=HOST,
            port=PORT,
            log_level="warning",
            access_log=False,
        )
        _server = uvicorn.Server(config)
        _server.run()
    except Exception as exc:
        _log_crash(exc)


def _on_quit(icon=None, item=None) -> None:
    global _server, _icon
    if _server is not None:
        _server.should_exit = True
    if _icon is not None:
        _icon.stop()


def main() -> None:
    global _icon

    if not _port_free(HOST, PORT):
        webbrowser.open(URL)
        return

    threading.Thread(target=_run_server, daemon=True, name="vlh-uvicorn").start()
    if not _wait_ready():
        _log_crash(RuntimeError("VLH server failed to start on port %s" % PORT))
        return

    _open_ui()

    menu = pystray.Menu(
        pystray.MenuItem("Open VLH UI", _open_ui, default=True),
        pystray.MenuItem("Close", _on_quit),
    )
    _icon = pystray.Icon("VLH", _make_tray_image(), "VideoEngineer's Little Helper", menu)
    _icon.run()

    if _server is not None:
        _server.should_exit = True
        time.sleep(0.3)


if __name__ == "__main__":
    freeze_support()
    try:
        main()
    except Exception as exc:
        _log_crash(exc)
        sys.exit(1)
