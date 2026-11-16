"""Prepare an isolated fixed-seed copy for MuMu play-through."""
import json, shutil, sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tools'))
from build_offline_worker import build
game=root/'analysis/level25_gen_opt_play/game'
shutil.copytree(root/'game',game,dirs_exist_ok=True)
path=game/'level-config.js'
config=json.loads(path.read_text(encoding='utf8').split('=',1)[1].strip().removesuffix(';'))
next(e for e in config['levels'] if e['level']==25)['generator']['seed']=553
path.write_text('window.oneConnectLevels='+json.dumps(config,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf8')
print('isolated level25 seed 553',*build(game))
