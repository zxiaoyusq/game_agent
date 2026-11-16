"""Rebuild the isolated copy using the unchanged shipping game and level configuration."""
import shutil, sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tools'))
from build_offline_worker import build
game=root/'analysis/level25_deadlock_subset/game'
shutil.copytree(root/'game',game,dirs_exist_ok=True)
print('level25 isolated shipping copy',*build(game))
