import json
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as temp:
    config = Path(temp) / 'levels.json'
    config.write_text(json.dumps({'levels': [{'level': 1, 'board': [[1, 1]]}]}), encoding='utf-8')
    def run(*args):
        return subprocess.run([sys.executable, str(root / 'tools/board_solver.py'), str(config), *args], capture_output=True, text=True)
    advisory = run('--max-nodes', '0')
    assert advisory.returncode == 0 and json.loads(advisory.stdout)[0]['status'] == 'unknown'
    strict = run('--max-nodes', '0', '--fail-on', 'invalid,unknown')
    assert strict.returncode == 1 and json.loads(strict.stdout)[0]['status'] == 'unknown'
    config.write_text(json.dumps({'levels': [{'level': 1, 'board': [[1], [1, 1]]}]}), encoding='utf-8')
    invalid = run('--fail-on', 'invalid')
    assert invalid.returncode == 1 and json.loads(invalid.stdout)[0]['status'] == 'invalid'
    assert run('--fail-on', 'typo').returncode != 0
print('solver distinguishes advisory unknown from requested failure statuses PASS')
