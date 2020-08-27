# -*- mode: python ; coding: utf-8 -*-

import os
block_cipher = None

a = Analysis(
	['TranslationToolkit.py'],
	pathex=[os.getcwd()],
	binaries=[],
	datas=[],
	hiddenimports=[],
	hookspath=[],
	runtime_hooks=[],
	excludes=[],
	win_no_prefer_redirects=False,
	win_private_assemblies=False,
	cipher=block_cipher,
	noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
	pyz,
	a.scripts,
	a.binaries,
	a.zipfiles,
	a.datas,
	[],
	name='TranslationToolkit',
	debug=False,
	bootloader_ignore_signals=False,
	strip=False,
	upx=True,
	upx_exclude=[],
	runtime_tmpdir=None,
	console=True,
	icon='Resources\\Images\\icon.ico'
)

"""
exe = EXE(
	pyz,
	a.scripts,
	[],
	exclude_binaries=True,
	name='TranslationToolkit',
	debug=False,
	bootloader_ignore_signals=False,
	strip=False,
	upx=True,
	console=True,
	icon='Resources\\Images\\icon.ico'
)
coll = COLLECT(
	exe,
	a.binaries,
	a.zipfiles,
	a.datas,
	strip=False,
	upx=True,
	upx_exclude=[],
	name='TranslationToolkit'
)
"""
