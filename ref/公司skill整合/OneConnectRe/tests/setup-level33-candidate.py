"""Build an isolated level 33 candidate from the decoded Shape61 mask."""
import csv, json, shutil, subprocess, sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = Path('E:/codex_apk_work/竞品拆解/tile connect/config/shapes_masks.csv')
with source.open(encoding='utf-8-sig', newline='') as stream:
    row = next(r for r in csv.DictReader(stream) if r['file'] == 'Shape61.txt')
raw = row['mask']
assert row['row'] == '6' and row['col'] == '9' and len(raw) == 54 and raw.count('0') == 44
mask = [[0] + [int(c == '0') for c in raw[i*9:(i+1)*9]] + [0, 0] for i in range(6)]
entry = {'level':33,'seconds':146,'theme':1,'movement':'gravity_up',
         'gravity':{'top':2,'left':0,'rows':9,'cols':6},
         'generator':{'mask':mask,'typeCount':22},'autoShuffle':'free'}
config = json.loads((root/'config/levels.json').read_text(encoding='utf-8'))
config['levels'] = sorted([e for e in config['levels'] if e['level'] != 33] + [entry], key=lambda e:e['level'])
target = root/'analysis/level33_up_candidate'
shutil.copytree(root/'game',target/'game',dirs_exist_ok=True)
target.joinpath('levels.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
subprocess.run([sys.executable,str(root/'tools/compile_levels.py'),'--config',str(target/'levels.json'),'--output',str(target/'game/data.js')],cwd=root,check=True)
subprocess.run([sys.executable,str(root/'tools/build_offline_worker.py'),'--game-dir',str(target/'game')],cwd=root,check=True)
