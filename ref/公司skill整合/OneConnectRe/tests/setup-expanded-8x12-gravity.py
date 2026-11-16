"""Build isolated fixed full-board samples; no shipping level is changed."""
import json, os, shutil, subprocess, sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
compiler=Path(os.environ.get('OC_COMPILER_PATH',root/'tools/compile_levels.py'))
for direction in ('up','down','left','right'):
 base=root/'analysis'/('expanded_8x12_gravity_'+direction);game=base/'game'
 shutil.copytree(root/'game',game,dirs_exist_ok=True)
 entry={'level':16,'seconds':600,'movement':'gravity_'+direction,'boardSize':{'rows':8,'cols':12,'itemSize':65,'spacing':5,'offsetX':220,'offsetY':100},'gravity':{'top':0,'left':0,'rows':12,'cols':8},'board':[[x//2+1 for x in range(12)] for _ in range(8)],'autoShuffle':'free'}
 cfg=base/'levels.json';cfg.write_text(json.dumps({'levels':[entry]},indent=2)+'\n',encoding='utf8')
 subprocess.run([sys.executable,str(compiler),'--config',str(cfg),'--output',str(game/'data.js')],cwd=root,check=True)
