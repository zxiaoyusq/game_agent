"""Build a fixed-seed generated 8x12 upward sample without changing production levels."""
import json,shutil,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];base=root/'analysis/expanded_8x12_generated_up';game=base/'game'
shutil.copytree(root/'game',game,dirs_exist_ok=True)
entry={'level':16,'seconds':600,'movement':'gravity_up','boardSize':{'rows':8,'cols':12,'itemSize':65,'spacing':5,'offsetX':220,'offsetY':100},'gravity':{'top':0,'left':0,'rows':12,'cols':8},'generator':{'mask':[[1]*12 for _ in range(8)],'typeCount':15,'seed':42},'autoShuffle':'free'}
cfg=base/'levels.json';cfg.write_text(json.dumps({'levels':[entry]},indent=2)+'\n',encoding='utf8')
subprocess.run([sys.executable,str(root/'tools/compile_levels.py'),'--config',str(cfg),'--output',str(game/'data.js')],cwd=root,check=True)
