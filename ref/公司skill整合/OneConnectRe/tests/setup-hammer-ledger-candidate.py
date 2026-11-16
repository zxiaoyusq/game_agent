"""Prepare an isolated experimental ledger; never modifies the shipping game."""
import shutil, sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tools'))
from build_offline_worker import build
base=root/'analysis/hammer_ledger_candidate'
game=base/'game'
shutil.copytree(root/'game',game,dirs_exist_ok=True)
for name in ('hammer-stock.js','hammer-runtime.js','reward-lifecycle.js'):
    shutil.copyfile(root/'examples/hammer-ledger-candidate'/name,game/name)
shutil.copyfile(root/'examples/hammer-ledger-candidate/reward-hammer-local.js',base/'reward-hammer-local.js')
html=game/'game.html';s=html.read_text(encoding='utf8');needle='<script src="hammer-runtime.js"></script>'
if needle not in s: raise RuntimeError('hammer script insertion point missing')
html.write_text(s.replace(needle,'<script src="hammer-stock.js"></script>\n    '+needle,1),encoding='utf8')
print('isolated candidate',*build(game))
