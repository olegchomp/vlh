"""VLH FastAPI app: REST API, static UI, OSC worker."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.paths import STATIC_DIR
from backend.state import store
from backend.worker import worker_loop

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("vlh")


class OscSettings(BaseModel):
    host: str = "127.0.0.1"
    port: int = Field(default=9000, ge=1, le=65535)


@asynccontextmanager
async def lifespan(app: FastAPI):
    store.load()
    stop_event = asyncio.Event()
    task = asyncio.create_task(worker_loop(stop_event))
    app.state.worker_stop = stop_event
    app.state.worker_task = task
    log.info("State loaded; worker running")
    yield
    stop_event.set()
    await task


app = FastAPI(title="VLH", lifespan=lifespan)


@app.get("/api/state")
def get_state() -> dict[str, Any]:
    return store.snapshot()


@app.put("/api/tasks")
def put_tasks(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    return store.replace_tasks(tasks)


@app.put("/api/timers")
def put_timers(timers: list[dict[str, Any]]) -> dict[str, Any]:
    return store.replace_timers(timers)


@app.put("/api/settings/osc")
def put_osc(body: OscSettings) -> dict[str, Any]:
    return store.update_osc(body.host, body.port)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
