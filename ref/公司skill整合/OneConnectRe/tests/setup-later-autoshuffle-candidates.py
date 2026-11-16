"""Rebuild isolated MuMu fixtures without touching the shipping game."""
import json
import shutil
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'tools'))
from build_offline_worker_candidate import build

fixture = json.loads((root / 'tests/fixtures/level29-deadlock-expanded.json').read_text(encoding='utf8'))
for name in ('level29_auto_candidate', 'level29_migration_old', 'level29_migration_new'):
    target = root / 'analysis' / name / 'game'
    shutil.copytree(root / 'game', target, dirs_exist_ok=True)
    config_file = target / 'level-config.js'
    content = config_file.read_text(encoding='utf8')
    config = json.loads(content.split('=', 1)[1].strip().removesuffix(';'))
    if name == 'level29_auto_candidate':
        config = fixture
    elif name == 'level29_migration_old':
        next(x for x in config['levels'] if x['level'] == 29).pop('autoShuffle', None)
    config_file.write_text('window.oneConnectLevels=' + json.dumps(config, ensure_ascii=False, separators=(',', ':')) + ';\n', encoding='utf8')
    print(name, *build(target))
