"""Prepare an isolated current-game copy for controlled deadlock testing."""
import shutil,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tools'))
from build_offline_worker import build
target=root/'analysis/level13_14_deadlock/game'
shutil.copytree(root/'game',target,dirs_exist_ok=True)
print('isolated level 13/14 deadlock copy',*build(target))
