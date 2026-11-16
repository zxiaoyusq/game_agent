"""Create isolated old/new copies for the session-safe worker test."""
import shutil, subprocess, sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
base=root/'analysis/cache_safe_candidate'
for name in ('live','new'):
    shutil.copytree(root/'game',base/name/'game',dirs_exist_ok=True)
for name in ('data.js','level-config.js'):
    (base/'live/game'/name).write_bytes(subprocess.check_output(['git','show',f'199ba0d:game/{name}'],cwd=root))
for name in ('live','new'):
    subprocess.run([sys.executable,str(root/'tools/build_offline_worker.py'),'--game-dir',str(base/name/'game')],cwd=root,check=True)
