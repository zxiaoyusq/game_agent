"""Snapshot provisional cfgLevels.score values; their link to B is unverified."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(r'E:\codex_apk_work\竞品拆解\tile connect\config\cfgLevels.csv')
OUT = ROOT / 'config' / 'competitor_star_reference.js'

def build():
    raw = SOURCE.read_bytes()
    values = {}
    with SOURCE.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames.count('level') != 1 or reader.fieldnames.count('score') != 1:
            raise ValueError('Expected unambiguous level and score columns')
        for item in reader:
            level, base = int(item['level']), int(item['score'])
            if level < 1 or base < 1 or str(level) in values:
                raise ValueError(f'Invalid or duplicate level {level}')
            values[str(level)] = [base, base + base // 2, base * 2]
    if len(values) != 500 or set(values) != {str(x) for x in range(1, 501)}:
        raise ValueError('Expected exactly levels 1–500; refusing partial output')
    data = {'source': 'cfgLevels.score', 'baseVerified': False, 'sha256': hashlib.sha256(raw).hexdigest(),
            'unit': 'competitor fly-star count', 'levels': values}
    OUT.write_text('/* Competitor reference; used only by isolated candidate builds. */\nwindow.oneConnectCompetitorStarReference = ' +
                   json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n', encoding='utf-8', newline='\n')
    print(f'{OUT}: {len(values)} levels')

if __name__ == '__main__':
    build()
