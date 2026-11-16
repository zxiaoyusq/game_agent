"""Prepare an isolated level 21 candidate with a previously failing seed."""
import json,shutil,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tools'))
from build_offline_worker import build
game=root/'analysis/level21_retry_candidate/game'
shutil.copytree(root/'analysis/level21_partial_candidate/game',game,dirs_exist_ok=True)
path=game/'level-config.js';config=json.loads(path.read_text(encoding='utf8').split('=',1)[1].strip().removesuffix(';'))
next(e for e in config['levels'] if e['level']==21)['generator']['seed']=240
path.write_text('window.oneConnectLevels='+json.dumps(config,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf8')
print('isolated level21 seed 240',*build(game))
