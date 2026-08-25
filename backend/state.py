"""In-memory state with atomic JSON persistence."""

from __future__ import annotations

import copy
import json
import shutil
import threading
import uuid
from pathlib import Path
from typing import Any, Callable

from backend.paths import DATA_DIR, SEED_STATE_PATH, STATE_PATH

DEFAULT_STATE: dict[str, Any] = {
    "settings": {"osc": {"host": "127.0.0.1", "port": 9000}},
    "tasks": [],
    "timers": [],
}


def _new_id() -> str:
    return str(uuid.uuid4())


def ensure_task_ids(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for t in tasks:
        item = dict(t)
        if not item.get("id"):
            item["id"] = _new_id()
        if "last_fired" not in item:
            item["last_fired"] = None
        out.append(item)
    return out


def ensure_timer_ids(timers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for t in timers:
        item = dict(t)
        if not item.get("id"):
            item["id"] = _new_id()
        out.append(item)
    return out


class StateStore:
    def __init__(self, path: Path = STATE_PATH) -> None:
        self.path = path
        self._lock = threading.RLock()
        self._data: dict[str, Any] = copy.deepcopy(DEFAULT_STATE)

    def load(self) -> None:
        with self._lock:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            if not self.path.exists():
                if SEED_STATE_PATH.exists():
                    shutil.copy2(SEED_STATE_PATH, self.path)
                else:
                    self._data = copy.deepcopy(DEFAULT_STATE)
                    self._save_unlocked()
                    return
            with self.path.open("r", encoding="utf-8") as f:
                raw = json.load(f)
            self._data = {
                "settings": {
                    "osc": {
                        "host": str(
                            raw.get("settings", {}).get("osc", {}).get("host", "127.0.0.1")
                        ),
                        "port": int(raw.get("settings", {}).get("osc", {}).get("port", 9000)),
                    }
                },
                "tasks": ensure_task_ids(list(raw.get("tasks") or [])),
                "timers": ensure_timer_ids(list(raw.get("timers") or [])),
            }

    def _save_unlocked(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".json.tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        tmp.replace(self.path)

    def save(self) -> None:
        with self._lock:
            self._save_unlocked()

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return copy.deepcopy(self._data)

    def replace_tasks(self, tasks: list[dict[str, Any]]) -> dict[str, Any]:
        with self._lock:
            old_by_id = {t.get("id"): t for t in self._data["tasks"] if t.get("id")}
            normalized = ensure_task_ids(tasks)
            for item in normalized:
                client = next((c for c in tasks if c.get("id") == item["id"]), None)
                if client is not None and "last_fired" not in client:
                    prev = old_by_id.get(item["id"])
                    if prev is not None:
                        item["last_fired"] = prev.get("last_fired")
            self._data["tasks"] = normalized
            self._save_unlocked()
            return copy.deepcopy(self._data)

    def replace_timers(self, timers: list[dict[str, Any]]) -> dict[str, Any]:
        with self._lock:
            self._data["timers"] = ensure_timer_ids(timers)
            self._save_unlocked()
            return copy.deepcopy(self._data)

    def update_osc(self, host: str, port: int) -> dict[str, Any]:
        with self._lock:
            self._data["settings"]["osc"] = {"host": host, "port": int(port)}
            self._save_unlocked()
            return copy.deepcopy(self._data)

    def mutate_tasks(self, mutator: Callable[[list[dict[str, Any]]], bool]) -> None:
        with self._lock:
            if mutator(self._data["tasks"]):
                self._save_unlocked()

    def get_osc(self) -> tuple[str, int]:
        with self._lock:
            osc = self._data["settings"]["osc"]
            return str(osc["host"]), int(osc["port"])

    def get_tasks_and_timers(
        self,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        with self._lock:
            return copy.deepcopy(self._data["tasks"]), copy.deepcopy(self._data["timers"])


store = StateStore()
