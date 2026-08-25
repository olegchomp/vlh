# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for VLH (onedir)."""

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None
root = Path(".").resolve()

hidden = []
hidden += collect_submodules("uvicorn")
hidden += collect_submodules("anyio")
hidden += collect_submodules("starlette")
hidden += collect_submodules("fastapi")

a = Analysis(
    [str(root / "run.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(root / "static"), "static"),
        (str(root / "data" / "state.json"), "data"),
    ],
    hiddenimports=hidden
    + [
        "backend",
        "backend.main",
        "backend.state",
        "backend.worker",
        "backend.osc_client",
        "backend.paths",
        "pythonosc",
        "pythonosc.udp_client",
        "pystray",
        "pystray._win32",
        "PIL",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.http.h11_impl",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="VLH",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="VLH",
)
