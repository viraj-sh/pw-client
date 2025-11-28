import sys
from PyInstaller.utils.hooks import collect_submodules

hidden = collect_submodules('fastapi') + collect_submodules('uvicorn')

block_cipher = None

a = Analysis(
    ['launcher.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('frontend', 'frontend'),
        ('schema', 'schema'),
        ('frontend/src/favicon.ico', 'frontend/src'),
    ],
    hiddenimports=hidden,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='pw-client',
    debug=False,
    strip=False,
    upx=False,
    console=True,
    icon='frontend/src/favicon.ico',
)

