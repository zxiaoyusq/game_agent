"""Build partial level 19: shape/time only; bombs and dual direction unknown."""
import csv,json,shutil,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
with Path('E:/codex_apk_work/竞品拆解/tile connect/config/shapes_masks.csv').open(encoding='utf-8-sig',newline='') as f:
 row=next(x for x in csv.DictReader(f) if x['file']=='Shape10.txt')
raw=row['mask'];assert row['row']=='7' and row['col']=='8' and len(raw)==56 and raw.count('0')==42
mask=[[int(c=='0') for c in raw[i*8:(i+1)*8]] for i in range(7)]+[[0]*8]
entry={'level':19,'seconds':211,'theme':2,'movement':'static',
 'boardSize':{'rows':8,'cols':8,'itemSize':75,'spacing':5,'offsetX':320,'offsetY':35},
 'generator':{'mask':mask,'typeCount':17},'autoShuffle':'free'}
config=json.loads((root/'config/levels.json').read_text(encoding='utf8'))
config['levels']=sorted([x for x in config['levels'] if x['level']!=19]+[entry],key=lambda x:x['level'])
target=root/'analysis/level19_partial_candidate';shutil.copytree(root/'game',target/'game',dirs_exist_ok=True)
(target/'levels.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
subprocess.run([sys.executable,str(root/'tools/compile_levels.py'),'--config',str(target/'levels.json'),'--output',str(target/'game/data.js')],cwd=root,check=True)
