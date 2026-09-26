# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None

# Корень проекта
ROOT = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    [os.path.join(ROOT, 'run.py')],
    pathex=[ROOT],
    binaries=[],
    datas=[
        (os.path.join(ROOT, 'assets'), 'assets'),
        (os.path.join(ROOT, 'doc_tpu', 'templates'), 'doc_tpu/templates'),
    ],
    hiddenimports=[
        'click',
        'docx',
        'docx.opc',
        'docx.opc.part',
        'docx.opc.packuri',
        'docx.oxml',
        'docx.oxml.ns',
        'docx.oxml.text',
        'docx.text',
        'docx.text.paragraph',
        'docx.table',
        'docx.section',
        'docx.shared',
        'docx.enum',
        'docx.enum.text',
        'docx.enum.table',
        'docx.enum.section',
        'lxml',
        'lxml.etree',
        'lxml._elementpath',
        'fpdf',
        'fpdf2',
        'PIL',
        'PIL.Image',
        'fontTools',
        'pptx',
        'pptx.util',
        'pptx.dml',
        'pptx.oxml',
        'mistune',
        'mistune.plugins',
        'mistune.plugins.table',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[os.path.join(ROOT, 'hook-docx.py')],
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
    name='doc-tpu',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
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
    name='doc-tpu',
)
