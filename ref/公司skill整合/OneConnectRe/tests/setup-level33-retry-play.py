"""Set a previously failing seed on the isolated level 33 candidate."""
import json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tools'))
from build_offline_worker import build
game=root/'analysis/level33_up_candidate/game'
path=game/'level-config.js'
config=json.loads(path.read_text(encoding='utf8').split('=',1)[1].strip().removesuffix(';'))
next(e for e in config['levels'] if e['level']==33)['generator']['seed']=97
path.write_text('window.oneConnectLevels='+json.dumps(config,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf8')
print('isolated level33 seed 97',*build(game))
