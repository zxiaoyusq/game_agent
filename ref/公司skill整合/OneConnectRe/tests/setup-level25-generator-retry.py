"""Isolated one-shot generation failure; production files remain unchanged."""
import shutil,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tools'))
from build_offline_worker import build
game=root/'analysis/level25_generator_retry/game'
shutil.copytree(root/'game',game,dirs_exist_ok=True)
p=game/'gravity-generator.js'
with p.open('a',encoding='utf8') as f:
    f.write("\n(function(){var original=oneConnectGravityGenerator.generate;oneConnectGravityGenerator.generate=function(){if(!sessionStorage.getItem('oc.test.once25')){sessionStorage.setItem('oc.test.once25','1');throw Error('controlled generation failure')}return original.apply(this,arguments)}}());\n")
print('isolated one-shot generation failure',*build(game))
