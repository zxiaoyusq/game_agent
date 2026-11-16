"""Create the isolated MuMu copy used by tutorial background tests."""
import shutil,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tools'))
from build_offline_worker_candidate import build
target=root/'analysis'/'tutorial_pause_candidate'/'game'
shutil.copytree(root/'game',target,dirs_exist_ok=True)
print('tutorial pause candidate',*build(target))
