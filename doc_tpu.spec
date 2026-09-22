# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec для doc-tpu — standalone бинарник."""
from PyInstaller.utils.hooks import collect_data_files

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('statics', 'statics'),
        ('template.snj', '.'),
    ] + collect_data_files('docx', include_py_files=False),
    hiddenimports=[
        'click',
        'docx',
        'docx.opc.constants',
        'docx.opc.exceptions',
        'docx.opc.packuri',
        'docx.opc.part',
        'docx.oxml',
        'docx.oxml.ns',
        'docx.shared',
        'docx.text.paragraph',
        'docx.text.run',
        'lxml',
        'lxml.etree',
        'fpdf',
        'PIL',
        'fontTools',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['hook-docx.py'],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='doc-tpu',
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
    icon=None,
)
