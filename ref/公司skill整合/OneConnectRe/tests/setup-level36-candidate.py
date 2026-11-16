"""Build a partial level 36 from Shape125; bomb and prop fields remain unknown."""
import csv,json,shutil,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
with Path('E:/codex_apk_work/竞品拆解/tile connect/config/shapes_masks.csv').open(encoding='utf-8-sig',newline='') as f:
 row=next(x for x in csv.DictReader(f) if x['file']=='Shape125.txt')
raw=row['mask'];assert row['row']=='7' and row['col']=='10' and len(raw)==70 and raw.count('0')==42
mask=[[int(c=='0') for c in raw[i*10:(i+1)*10]] for i in range(7)]+[[0]*10]
entry={'level':36,'seconds':138,'theme':2,'movement':'gravity_up',
 'boardSize':{'rows':8,'cols':10,'itemSize':75,'spacing':5,'offsetX':240,'offsetY':35},
 'gravity':{'top':0,'left':0,'rows':10,'cols':7},'generator':{'mask':mask,'typeCount':21},'autoShuffle':'free'}
config=json.loads((root/'config/levels.json').read_text(encoding='utf8'))
config['levels']=sorted([x for x in config['levels'] if x['level']!=36]+[entry],key=lambda x:x['level'])
target=root/'analysis/level36_partial_candidate';shutil.copytree(root/'game',target/'game',dirs_exist_ok=True)
(target/'levels.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
subprocess.run([sys.executable,str(root/'tools/compile_levels.py'),'--config',str(target/'levels.json'),'--output',str(target/'game/data.js')],cwd=root,check=True)
