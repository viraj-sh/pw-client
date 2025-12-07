import sys
import os
from PyInstaller.utils.hooks import collect_submodules

spec_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
project_root = os.path.abspath(os.path.join(spec_dir, '..'))

hidden = collect_submodules('fastapi') + collect_submodules('uvicorn')

block_cipher = None

a = Analysis(
    [os.path.join(project_root, 'launcher.py')],
    pathex=[project_root, os.path.join(project_root, 'app')],
    binaries=[],
    datas=[
        (os.path.join(project_root, 'app/static'), 'static'),
        (os.path.join(project_root, 'app/core'), 'app/core'),
        (os.path.join(project_root, 'app/api'), 'app/api'),
        (os.path.join(project_root, 'app/schema'), 'app/schema'),
        (os.path.join(project_root, 'app/static/assets/favicon.ico'), 'static/src'),
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
    [],
    name='pw-client',
    debug=False,
    strip=False,
    upx=False,
    console=True,
    icon=os.path.join(project_root, 'app/static/assets/favicon.ico'),
)
