# VideoEngineer's Little Helper (VLH)

Scheduler and timer tool for video engineers. Web UI talks to a local Python backend that keeps state in memory, persists to JSON, and sends **OSC** over UDP.

v.1.0.0 · [@VJSCHOOL](https://t.me/vjschool)

## Features

- **Scheduler** — Once / Daily / Weekly / Monthly tasks → OSC address + value
- **Timers** — Count Up / Countdown with format presets → OSC string each second when active
- **OSC target** — host/port in the sidebar (default `127.0.0.1:9000`)
- **Persistence** — `data/state.json` on every change; reload on F5
- **Desktop** — tray app (`Open VLH UI` / `Close`), no console window

## Requirements

- Windows
- Python 3.11+ (for development)
- Dependencies: see [`requirements.txt`](requirements.txt)

## Development

From the parent folder that contains `.venv` and `vlh/`:

```powershell
cd F:\VJSCHOOL\VLH
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r vlh\requirements.txt
```

If `pip` hangs on `pypi.ngc.nvidia.com`, temporarily clear the NVIDIA `extra-index-url` in `C:\ProgramData\pip\pip.ini` (or use [`build_exe.ps1`](build_exe.ps1), which does this for the build).

Run the API + UI:

```powershell
cd F:\VJSCHOOL\VLH
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --app-dir vlh --host 127.0.0.1 --port 8765 --reload
```

Open [http://127.0.0.1:8765/](http://127.0.0.1:8765/).

Or run the tray entry (opens the browser):

```powershell
cd F:\VJSCHOOL\VLH\vlh
..\.venv\Scripts\python.exe run.py
```
## Build EXE

```powershell
cd F:\VJSCHOOL\VLH\vlh
.\build_exe.ps1
```

Output: `dist\VLH\VLH.exe` — distribute the **whole** `dist\VLH\` folder.

- Double-click `VLH.exe` → tray icon + browser UI
- Writable state: `dist\VLH\data\state.json` (created next to the exe)

## Project layout

```
vlh/
  backend/       FastAPI, state, OSC worker
  static/        Web UI
  data/          Seed / default state.json
  run.py         Tray + server entry
  vlh.spec       PyInstaller
  build_exe.ps1  Build script
```

## API (local)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/state` | Full state |
| PUT | `/api/tasks` | Replace tasks list |
| PUT | `/api/timers` | Replace timers list |
| PUT | `/api/settings/osc` | `{ "host", "port" }` |

## OSC value parsing

Task `value` field:

- empty → address only
- `true` / `false` → bool
- integer / float → number
- otherwise → string

Timers send the formatted time string as one OSC argument.
