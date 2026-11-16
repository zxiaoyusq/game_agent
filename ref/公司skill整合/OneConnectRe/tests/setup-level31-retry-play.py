"""Prepare fixed-seed device test for the isolated retry candidate."""
import json, shutil, sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tools'))
from build_offline_worker import build
game=root/'analysis/level31_retry_candidate/game'
shutil.copytree(root/'game',game,dirs_exist_ok=True)
path=game/'level-config.js'
config=json.loads(path.read_text(encoding='utf8').split('=',1)[1].strip().removesuffix(';'))
next(e for e in config['levels'] if e['level']==31)['generator']['seed']=486
path.write_text('window.oneConnectLevels='+json.dumps(config,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf8')
print('isolated level31 seed 486',*build(game))
