import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
from ramadan_animation_candidate import add_ramadan_animation


class RamadanAnimationTest(unittest.TestCase):
    def test_frames_are_distinct_and_source_is_unchanged(self):
        source = json.loads((ROOT / 'baseline/data.js').read_text(encoding='utf8'))
        original = copy.deepcopy(source)
        result = add_ramadan_animation(source, 'images/ramadan-tiles.png', 1234, 987654321234567)
        self.assertEqual(source, original)
        frames = result['project'][3][5][7][3][7]
        self.assertEqual(len(frames), 20)
        self.assertEqual(len({tuple(f[2:6]) for f in frames}), 20)
        self.assertEqual(frames[-1][2:6], [393, 295, 96, 96])
        rebuilt = add_ramadan_animation(result, 'images/ramadan-tiles.png', 1234, 987654321234567)
        self.assertEqual(result, rebuilt, 'rebuilding the same theme must be idempotent')
        with self.assertRaises(ValueError): add_ramadan_animation(result, 'images/ramadan-tiles.png', 1234, 123456)


if __name__ == '__main__': unittest.main()
