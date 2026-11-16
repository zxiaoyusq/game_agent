import json
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from board_solver import find_solution

class FiveMovementLevels(unittest.TestCase):
    def test_five_modes_produce_complete_paths(self):
        data=json.loads((ROOT/'config/five-movement-validation.json').read_text(encoding='utf-8-sig'))
        self.assertEqual([entry['level'] for entry in data['levels']], [1,2,3,4,5])
        for entry, mode in zip(data['levels'], ['static','fall_down','fall_up','move_right','move_left']):
            with self.subTest(level=entry['level'], mode=mode):
                result=find_solution(entry['board'], max_nodes=10000, mode=mode)
                self.assertEqual(result['status'], 'solved')
                self.assertEqual(len(result['moves']), 36)

if __name__ == '__main__':
    unittest.main()
