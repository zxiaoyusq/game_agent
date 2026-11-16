"""Build the isolated level 25 candidate from the extracted mask and current config."""
import csv, json, shutil, subprocess, sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = Path('E:/codex_apk_work/竞品拆解/tile connect/config/shape_masks_L1-L30.csv')
with source.open(encoding='utf-8-sig', newline='') as stream:
    row = next(r for r in csv.DictReader(stream) if r['level'] == '25')
lines = row['mask_rows'].split('/')
assert row['shapeid'] == '34' and len(lines) == 7 and all(len(x) == 10 for x in lines)
mask = [[int(c == '#') for c in line] for line in lines] + [[0] * 10]
assert sum(map(sum, mask)) == 60
config = json.loads((root / 'config/levels.json').read_text(encoding='utf-8'))
config['levels'] = [e for e in config['levels'] if e['level'] != 25]
config['levels'].append({'level':25,'seconds':233,'theme':1,'movement':'gravity_up',
    'boardSize':{'rows':8,'cols':10,'itemSize':75,'spacing':5,'offsetX':240,'offsetY':35},
    'gravity':{'top':0,'left':0,'rows':10,'cols':7},
    'generator':{'mask':mask,'typeCount':15},'autoShuffle':'free'})
config['levels'].sort(key=lambda x:x['level'])
target = root / 'analysis/level25_up_candidate'
shutil.copytree(root / 'game', target / 'game', dirs_exist_ok=True)
target.joinpath('levels.json').write_text(json.dumps(config, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
subprocess.run([sys.executable, str(root/'tools/compile_levels.py'), '--config', str(target/'levels.json'), '--output', str(target/'game/data.js')], cwd=root, check=True)
