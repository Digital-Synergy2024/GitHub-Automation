# -*- mode: python ; coding: utf-8 -*-
import os

# Get the absolute path to the icon file
icon_path = os.path.join(os.path.dirname(SPECPATH), "py", "assets", "Digital-Synergy.ico")


a = Analysis(
    ['github_manager.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['CTkListbox', 'customtkinter_listbox', 'requests', 'certifi', 'idna', 'urllib3', 'charset_normalizer', 'customtkinter'],
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
    a.binaries,
    a.datas,
    [],
    name='github_manager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)
