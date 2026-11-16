"""Prepare an isolated partial level 37; dual-direction rules are unknown."""
import argparse
import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path('E:/codex_apk_work/竞品拆解/tile connect/config/shapes_masks.csv')


def build(destination):
    target = Path(destination).resolve()
    analysis = (ROOT / 'analysis').resolve()
    if target == analysis or analysis not in target.parents:
        raise ValueError('destination must be inside analysis')
    target.mkdir(parents=True, exist_ok=False)
    with SOURCE.open(encoding='utf-8-sig', newline='') as stream:
        row = next(x for x in csv.DictReader(stream) if x['file'] == 'Shape17.txt')
    raw = row['mask']
    if (row['row'], row['col'], len(raw), raw.count('0')) != ('7', '9', 63, 44):
        raise ValueError('unexpected Shape17 data')
    mask = [[int(c == '0') for c in raw[i*9:(i+1)*9]] + [0] for i in range(7)] + [[0]*10]
    entry = {'level':37, 'seconds':146, 'theme':0, 'movement':'static',
        'boardSize':{'rows':8, 'cols':10, 'itemSize':75, 'spacing':5, 'offsetX':240, 'offsetY':35},
        'generator':{'mask':mask, 'typeCount':12}, 'autoShuffle':'free'}
    config = json.loads((ROOT / 'config/levels.json').read_text(encoding='utf8'))
    if any(item['level'] == 37 for item in config['levels']):
        raise ValueError('formal level 37 already exists')
    config['levels'].append(entry)
    config['levels'].sort(key=lambda item:item['level'])
    shutil.copytree(ROOT / 'game', target / 'game')
    (target / 'levels.json').write_text(json.dumps(config, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    subprocess.run([sys.executable, str(ROOT / 'tools/compile_levels.py'), '--config',
        str(target / 'levels.json'), '--output', str(target / 'game/data.js')], cwd=ROOT, check=True)
    print('Partial candidate:', target / 'game/game.html')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    build(parser.parse_args().output)
