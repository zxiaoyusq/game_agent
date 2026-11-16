"""Build an isolated MuMu game copy for original effect regression."""
import shutil,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'tools'))
from build_offline_worker_candidate import build
target=root/'analysis'/'effect_integrity_candidate'/'game'
shutil.copytree(root/'game',target,dirs_exist_ok=True)
print('effect integrity candidate',*build(target))
