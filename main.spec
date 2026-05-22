# -*- mode: python ; coding: utf-8 -*-
"""Especificação do PyInstaller para o DeepSeek Accountant & Tracker."""

import sys
from pathlib import Path

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("data", "data"),
    ],
    hiddenimports=[
        "matplotlib",
        "matplotlib.backends.backend_tkagg",
        "tkinter",
        "tkinter.ttk",
        "tkinter.filedialog",
        "tkinter.messagebox",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DeepSeek Tracker",
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
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="DeepSeek Tracker",
)
