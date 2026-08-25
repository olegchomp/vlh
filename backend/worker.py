"""Background scheduler and timer OSC loop (~1 Hz)."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from backend.osc_client import parse_osc_value, send_osc
from backend.state import store

log = logging.getLogger("vlh.worker")


def _normalize_time(time_str: str | None) -> str:
    t = time_str or "00:00:00"
    if len(t) == 5:
        return f"{t}:00"
    return t


def _minute_key(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M")


def _time_matches(task_time: str | None, now: datetime) -> bool:
    t = _normalize_time(task_time)
    try:
        parts = t.split(":")
        hh, mm = int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        return False
    return now.hour == hh and now.minute == mm


def _task_due(task: dict[str, Any], now: datetime) -> bool:
    if not task.get("active"):
        return False
    if not _time_matches(task.get("time"), now):
        return False

    kind = task.get("type") or "Once"
    if kind == "Once":
        date = task.get("date") or ""
        return date == now.strftime("%Y-%m-%d")
    if kind == "Daily":
        return True
    if kind == "Weekly":
        # UI: 0=Sunday .. 6=Saturday (matches datetime.weekday() where Mon=0
        # — HTML uses value "0" Sunday like JS getDay())
        try:
            wanted = int(task.get("weekday", "1"))
        except (TypeError, ValueError):
            return False
        # Python: Monday=0 .. Sunday=6 → convert to JS-style Sun=0
        js_weekday = (now.weekday() + 1) % 7
        return js_weekday == wanted
    if kind == "Monthly":
        try:
            day = int(task.get("monthDay", "1"))
        except (TypeError, ValueError):
            return False
        return now.day == day
    return False


def _pad2(n: float | int) -> str:
    return str(max(0, int(n))).zfill(2)


def format_by_parts(total_seconds: float, fmt: str) -> str:
    sec = max(0, int(total_seconds))
    dd = sec // 86400
    sec %= 86400
    hh = sec // 3600
    sec %= 3600
    mm = sec // 60
    ss = sec % 60

    if fmt == "HH:MM:SS":
        return f"{_pad2(dd * 24 + hh)}:{_pad2(mm)}:{_pad2(ss)}"
    if fmt == "MM:SS":
        return f"{_pad2(dd * 1440 + hh * 60 + mm)}:{_pad2(ss)}"
    if fmt == "SS":
        return str(dd * 86400 + hh * 3600 + mm * 60 + ss).zfill(2)
    return f"{_pad2(dd)}:{_pad2(hh)}:{_pad2(mm)}:{_pad2(ss)}"


def _parse_datetime(date: str | None, time_str: str | None) -> datetime:
    t = _normalize_time(time_str)
    d = date or "1970-01-01"
    try:
        return datetime.strptime(f"{d}T{t}", "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return datetime.now()


def timer_output_string(timer: dict[str, Any], now: datetime) -> str:
    target = _parse_datetime(timer.get("date"), timer.get("time"))
    if timer.get("type") == "Countdown":
        seconds = max(0.0, (target - now).total_seconds())
    else:
        seconds = max(0.0, (now - target).total_seconds())
    return format_by_parts(seconds, timer.get("format") or "DD:HH:MM:SS")


def _tick_once() -> None:
    now = datetime.now()
    minute = _minute_key(now)
    host, port = store.get_osc()
    tasks, timers = store.get_tasks_and_timers()
    dirty = False

    def mutate(task_list: list[dict[str, Any]]) -> bool:
        nonlocal dirty
        changed = False
        by_id = {t.get("id"): t for t in task_list}
        for snap in tasks:
            tid = snap.get("id")
            live = by_id.get(tid)
            if live is None:
                continue
            if not _task_due(live, now):
                continue
            if live.get("last_fired") == minute:
                continue
            address = str(live.get("command") or "/")
            args = parse_osc_value(live.get("value"))
            try:
                send_osc(host, port, address, *args)
                log.info("OSC task %s -> %s %s", live.get("name"), address, args)
            except Exception:
                log.exception("OSC send failed for task %s", live.get("name"))
            live["last_fired"] = minute
            if (live.get("type") or "Once") == "Once":
                live["active"] = False
            changed = True
            dirty = True
        return changed

    store.mutate_tasks(mutate)

    for timer in timers:
        if not timer.get("active"):
            continue
        address = str(timer.get("command") or "/")
        value = timer_output_string(timer, now)
        try:
            send_osc(host, port, address, value)
        except Exception:
            log.exception("OSC send failed for timer %s", timer.get("name"))

    if dirty:
        # mutate_tasks already saved when changed
        pass


async def worker_loop(stop_event: asyncio.Event) -> None:
    log.info("Worker started")
    while not stop_event.is_set():
        try:
            await asyncio.to_thread(_tick_once)
        except Exception:
            log.exception("Worker tick error")
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=1.0)
        except asyncio.TimeoutError:
            pass
    log.info("Worker stopped")
