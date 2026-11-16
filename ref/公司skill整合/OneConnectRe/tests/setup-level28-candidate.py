"""Build a partial level 28 from Shape23; bomb and prop fields remain unknown."""
import csv,json,shutil,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
with Path('E:/codex_apk_work/竞品拆解/tile connect/config/shapes_masks.csv').open(encoding='utf-8-sig',newline='') as f:
 row=next(x for x in csv.DictReader(f) if x['file']=='Shape23.txt')
raw=row['mask'];assert row['row']=='7' and row['col']=='9' and len(raw)==63 and raw.count('0')==44
mask=[[int(c=='0') for c in raw[i*9:(i+1)*9]+'1'] for i in range(7)]+[[0]*10]
entry={'level':28,'seconds':176,'theme':1,'movement':'static',
 'boardSize':{'rows':8,'cols':10,'itemSize':75,'spacing':5,'offsetX':240,'offsetY':35},
 'generator':{'mask':mask,'typeCount':22},'autoShuffle':'free'}
config=json.loads((root/'config/levels.json').read_text(encoding='utf8'))
config['levels']=sorted([x for x in config['levels'] if x['level']!=28]+[entry],key=lambda x:x['level'])
target=root/'analysis/level28_partial_candidate';shutil.copytree(root/'game',target/'game',dirs_exist_ok=True)
(target/'levels.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
subprocess.run([sys.executable,str(root/'tools/compile_levels.py'),'--config',str(target/'levels.json'),'--output',str(target/'game/data.js')],cwd=root,check=True)
