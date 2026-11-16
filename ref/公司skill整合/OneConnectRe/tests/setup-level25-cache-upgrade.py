"""Prepare disposable old/new builds to reproduce the cache activation boundary."""
import shutil, subprocess, sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
base = root/'analysis/level25_cache_upgrade'
for name in ('live', 'new'):
    shutil.copytree(root/'game', base/name/'game', dirs_exist_ok=True)
old = base/'live/game'
for name in ('data.js','level-config.js'):
    (old/name).write_bytes(subprocess.check_output(['git','show',f'199ba0d:game/{name}'],cwd=root))
legacy = base/'legacy_worker_builder.py'
legacy.write_bytes(subprocess.check_output(['git','show','199ba0d:tools/build_offline_worker.py'],cwd=root))
for name in ('live','new'):
    subprocess.run([sys.executable,str(legacy),'--game-dir',str(base/name/'game')],cwd=root,check=True)
