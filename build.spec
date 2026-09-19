# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置：内置 ffmpeg，输出 console 可执行文件（支持交互输入 UID）。"""
import os
import sys

project_root = os.path.abspath(SPECPATH)  # SPECPATH 即 spec 文件所在目录，本身已是目录

# 按平台选择 ffmpeg 二进制
if sys.platform == "darwin":
    ffmpeg_path = os.path.join(project_root, "bin", "ffmpeg")
elif sys.platform == "win32":
    ffmpeg_path = os.path.join(project_root, "bin", "ffmpeg.exe")
else:
    ffmpeg_path = os.path.join(project_root, "bin", "ffmpeg")

binaries = []
if os.path.exists(ffmpeg_path):
    binaries.append((ffmpeg_path, "bin"))

a = Analysis(
    ["run.py"],
    pathex=[project_root],
    binaries=binaries,
    datas=[],
    hiddenimports=[],
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
