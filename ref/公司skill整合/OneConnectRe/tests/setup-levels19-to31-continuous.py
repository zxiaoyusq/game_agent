"""Prepare an isolated shipping-code copy for the MuMu progression test."""
import shutil,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tools'))
from build_offline_worker import build
game=root/'analysis/levels19_to31_continuous/game'
shutil.copytree(root/'game',game,dirs_exist_ok=True)
print('isolated level 19-31 copy',*build(game))
