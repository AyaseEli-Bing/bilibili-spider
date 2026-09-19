# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置：输出 console 可执行文件（支持交互输入 UID）。"""
import os
import sys

project_root = os.path.abspath(SPECPATH)  # SPECPATH 即 spec 文件所在目录，本身已是目录

a = Analysis(
    ["run.py"],
    pathex=[project_root],
    binaries=[],
    datas=[],
    hiddenimports=["qrcode"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "unittest", "pydoc", "doctest"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="bilibili-spider",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
