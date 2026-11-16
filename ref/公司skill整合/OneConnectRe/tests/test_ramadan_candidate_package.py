"""Validate a built candidate's fourth theme against its atlas and cache manifest."""
import json
import os
from pathlib import Path
import unittest
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent


class RamadanCandidatePackage(unittest.TestCase):
    def test_latest_build_contains_complete_unique_frames(self):
        game = Path(os.environ.get('ONECONNECT_CANDIDATE', ROOT / 'analysis/ui_iteration_candidate_v77/game'))
        if not (game / 'data.js').exists(): self.skipTest('candidate build not present')
        data = json.loads((game / 'data.js').read_text(encoding='utf8'))
        animations = data['project'][3][5][7]
        self.assertEqual([(a[0], len(a[7])) for a in animations], [('t0', 30), ('t1', 30), ('t2', 30), ('t3', 20)])
        frames = animations[3][7]
        self.assertEqual(len({tuple(frame[2:6]) for frame in frames}), 20)
        atlas = game / 'images/ramadan-tiles.webp'
        with Image.open(atlas) as image:
            self.assertEqual(image.size, (512, 512))
        self.assertTrue(all(f[0] == 'images/ramadan-tiles.webp' and f[1] == atlas.stat().st_size for f in frames))
        self.assertIn('ramadan-tiles.webp', (game / 'offline-worker.js').read_text(encoding='utf8'))
        save = (game / 'round-save.js').read_text(encoding='utf8')
        board = (game / 'board-hooks.js').read_text(encoding='utf8')
        self.assertRegex(save, r'theme\.data<=3')
        self.assertIn('saved.theme <= 3', board)
        self.assertIn('return v>20;', board)


if __name__ == '__main__': unittest.main()
