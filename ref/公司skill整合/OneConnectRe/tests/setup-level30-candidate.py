"""Partial level 30: decoded mask and time; bombs/dual direction unknown."""
import csv,json,shutil,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
with Path('E:/codex_apk_work/竞品拆解/tile connect/config/shapes_masks.csv').open(encoding='utf-8-sig',newline='') as f:
 row=next(x for x in csv.DictReader(f) if x['file']=='Shape41.txt')
raw=row['mask'];assert row['row']=='7' and row['col']=='12' and len(raw)==84 and raw.count('0')==50
mask=[[int(c=='0') for c in raw[i*12:(i+1)*12]] for i in range(7)]+[[0]*12]
entry={'level':30,'seconds':258,'theme':0,'movement':'static',
 'boardSize':{'rows':8,'cols':12,'itemSize':65,'spacing':5,'offsetX':220,'offsetY':100},
 'generator':{'mask':mask,'typeCount':25},'autoShuffle':'free'}
config=json.loads((root/'config/levels.json').read_text(encoding='utf8'))
config['levels']=sorted([x for x in config['levels'] if x['level']!=30]+[entry],key=lambda x:x['level'])
target=root/'analysis/level30_partial_candidate';shutil.copytree(root/'game',target/'game',dirs_exist_ok=True)
(target/'levels.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
subprocess.run([sys.executable,str(root/'tools/compile_levels.py'),'--config',str(target/'levels.json'),'--output',str(target/'game/data.js')],cwd=root,check=True)
