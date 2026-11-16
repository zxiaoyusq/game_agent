"""Build a controlled deadlock fixture without changing shipping levels."""
import shutil,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];game=root/'analysis/expanded_8x12_deadlock_up/game'
shutil.copytree(root/'game',game,dirs_exist_ok=True)
subprocess.run([sys.executable,str(root/'tools/compile_levels.py'),'--config',str(root/'tests/fixtures/expanded-8x12-up-deadlock.json'),'--output',str(game/'data.js')],cwd=root,check=True)
