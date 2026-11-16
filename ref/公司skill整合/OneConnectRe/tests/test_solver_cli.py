import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

class SolverCliTests(unittest.TestCase):
    def test_original_mode_supports_configured_global_gravity(self):
        data = {'levels': [{'level': 7, 'seconds': 100, 'board': [[1, 2], [1, 2]],
                            'movement': 'gravity_down', 'gravity': {'top': 0, 'left': 0, 'rows': 2, 'cols': 2}}]}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'levels.json'
            path.write_text(json.dumps(data), encoding='utf8')
            proc = subprocess.run([sys.executable, str(ROOT/'tools/board_solver.py'), str(path), '--mode', 'original', '--fail-on', 'invalid'], capture_output=True, text=True, encoding='utf8', cwd=tmp)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(json.loads(proc.stdout)[0]['status'], 'solved')

    def test_original_mode_selects_all_five_movement_modes(self):
        data = {'levels': [{'level': 1, 'seconds': 100, 'board': [[1, 1]]},
                           {'level': 2, 'seconds': 100, 'board': [[1, 1]]},
                           {'level': 3, 'seconds': 100, 'board': [[1, 1]]},
                           {'level': 4, 'seconds': 100, 'board': [[1, 1]]},
                           {'level': 5, 'seconds': 100, 'board': [[1, 1]]}]}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'levels.json'
            path.write_text(json.dumps(data), encoding='utf8')
            proc = subprocess.run([sys.executable, str(ROOT/'tools/board_solver.py'), str(path), '--mode', 'original'], capture_output=True, text=True, encoding='utf8', check=True, cwd=tmp)
        result = json.loads(proc.stdout)
        self.assertEqual([r['mode'] for r in result], ['static', 'fall_down', 'fall_up', 'move_right', 'move_left'])
        self.assertEqual([r['status'] for r in result], ['solved', 'solved', 'solved', 'solved', 'solved'])

    def test_summary_omits_long_move_list(self):
        data = {'levels': [{'level': 1, 'seconds': 100, 'board': [[1, 1]]}]}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'levels.json'
            path.write_text(json.dumps(data), encoding='utf8')
            proc = subprocess.run([sys.executable, str(ROOT/'tools/board_solver.py'), str(path), '--mode', 'original', '--summary'], capture_output=True, text=True, encoding='utf8', check=True, cwd=tmp)
        result = json.loads(proc.stdout)
        self.assertEqual(result[0]['status'], 'solved')
        self.assertEqual(result[0]['move_count'], 1)
        self.assertNotIn('moves', result[0])

if __name__ == '__main__':
    unittest.main()
