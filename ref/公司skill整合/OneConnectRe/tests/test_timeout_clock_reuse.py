import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
spec = importlib.util.spec_from_file_location('candidate_builder', ROOT / 'tools/prepare_gameplay_layout_candidate.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class TimeoutClockReuseTest(unittest.TestCase):
    def test_reuses_red_clock_at_native_size_and_keeps_shake(self):
        source = ROOT / 'analysis/ui_iteration_candidate_v228_final/game'
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            (dest / 'images').mkdir()
            shutil.copyfile(source / 'data.js', dest / 'data.js')
            shutil.copyfile(source / 'asset-formats.json', dest / 'asset-formats.json')
            shutil.copyfile(source / 'images/timeout-clock.webp', dest / 'images/timeout-clock.webp')
            shutil.copyfile(source / 'images/timesup-sheet0.webp', dest / 'images/timesup-sheet0.webp')
            before = json.loads((dest / 'data.js').read_text(encoding='utf8'))
            shake = before['project'][3][51][8]
            builder.reuse_timeout_clock(dest)
            after = json.loads((dest / 'data.js').read_text(encoding='utf8'))
            sprite = after['project'][3][51]
            self.assertEqual(sprite[7][0][7][0][0], 'images/timeout-clock.webp')
            self.assertEqual(sprite[7][0][7][0][4:6], [320, 292])
            self.assertEqual(sprite[8], shake)
            self.assertEqual(json.loads((dest / 'asset-formats.json').read_text(encoding='utf8'))['images/timesup-sheet0.png'], 'images/timeout-clock.webp')
            self.assertEqual(after['project'][5][2][6][0][14][19][0][3:5], [320, 292])
            self.assertEqual(list((dest / 'images').iterdir()), [dest / 'images/timeout-clock.webp'])


if __name__ == '__main__':
    unittest.main()
