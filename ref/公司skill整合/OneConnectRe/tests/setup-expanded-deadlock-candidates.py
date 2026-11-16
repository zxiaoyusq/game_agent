"""Compile isolated 8x10 gravity/deadlock fixtures against the current game."""
import shutil,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
for direction in ('up','right'):
    game=root/'analysis'/('expanded_deadlock_'+direction)/'game'
    shutil.copytree(root/'game',game,dirs_exist_ok=True)
    cfg=root/'tests'/'fixtures'/('expanded-8x10-'+direction+'-deadlock.json')
    subprocess.run([sys.executable,str(root/'tools/compile_levels.py'),'--config',str(cfg),'--output',str(game/'data.js')],cwd=root,check=True)
