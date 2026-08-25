"""OSC value parsing and UDP send."""

from __future__ import annotations

from typing import Any

from pythonosc.udp_client import SimpleUDPClient


def parse_osc_value(raw: str | None) -> list[Any]:
    """Parse UI value string into OSC args. Empty -> no args."""
    if raw is None:
        return []
    text = str(raw).strip()
    if text == "":
        return []
    lower = text.lower()
    if lower == "true":
        return [True]
    if lower == "false":
        return [False]
    try:
        if text.isdigit() or (text.startswith("-") and text[1:].isdigit()):
            return [int(text)]
    except ValueError:
        pass
    try:
        if "." in text or "e" in lower:
            return [float(text)]
    except ValueError:
        pass
    # Prefer int over float for plain numbers already handled; try float last
    try:
        return [float(text)]
    except ValueError:
        return [text]


def send_osc(host: str, port: int, address: str, *args: Any) -> None:
    addr = (address or "/").strip() or "/"
    if not addr.startswith("/"):
        addr = "/" + addr
    client = SimpleUDPClient(host, int(port))
    client.send_message(addr, list(args) if args else [])
