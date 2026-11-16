import json
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from board_solver import find_solution

class FirstLevels(unittest.TestCase):
    def test_three_levels_are_well_formed_and_have_verified_solutions(self):
        data = json.loads((ROOT / 'config/first-level-candidate.json').read_text(encoding='utf-8-sig'))
        self.assertEqual([x['level'] for x in data['levels']], [1, 2, 3])
        for item, seconds, types, mode in zip(data['levels'], [180, 180, 163], [8, 9, 10], ['static', 'fall_down', 'fall_up']):
            self.assertEqual(item['seconds'], seconds)
            board = item['board']
            self.assertEqual((len(board), {len(row) for row in board}), (6, {12}))
            counts = Counter(n for row in board for n in row)
            self.assertEqual(len(counts), types)
            self.assertTrue(all(1 <= n <= 20 and count % 2 == 0 for n, count in counts.items()))
            self.assertEqual(find_solution(board, max_nodes=10000, mode=mode)['status'], 'solved')

if __name__ == '__main__':
    unittest.main()
