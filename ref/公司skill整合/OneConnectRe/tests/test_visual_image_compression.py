import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tools'))
spec = importlib.util.spec_from_file_location('candidate_builder', PROJECT / 'tools' / 'prepare_gameplay_layout_candidate.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class VisualImageCompressionTest(unittest.TestCase):
    def test_accepts_only_smaller_matching_source_and_alpha(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target, source, optimized = root / 'game', root / 'source', root / 'optimized'
            (target / 'images').mkdir(parents=True)
            source.mkdir()
            optimized.mkdir()
            rows = []
            for name in ('safe.png', 'alpha.png', 'stale.png', 'line-sheet0.png'):
                image = Image.new('RGBA', (32, 32), (150, 100, 50, 180))
                image.save(source / name, compress_level=0)
                image.save(target / 'images' / name, compress_level=0)
                if name == 'alpha.png':
                    image.putpixel((0, 0), (150, 100, 50, 0))
                image.save(optimized / name, optimize=True)
                if name == 'stale.png':
                    Image.new('RGBA', (32, 32), (5, 10, 15, 180)).save(target / 'images' / name, compress_level=0)
                rows.append({'path': str(source / name), 'status': 'compressed', 'ssim': 0.999, 'detail': {'ssim_p1': 0.99, 'residual': 1}})
            report = root / 'report.json'
            report.write_text(json.dumps(rows), encoding='utf8')
            original = {p.name: p.read_bytes() for p in (target / 'images').iterdir()}
            self.assertEqual(builder.apply_verified_visual_images(target, optimized, report, source), 1)
            self.assertEqual((target / 'images' / 'safe.png').read_bytes(), (optimized / 'safe.png').read_bytes())
            for name in ('alpha.png', 'stale.png', 'line-sheet0.png'):
                self.assertEqual((target / 'images' / name).read_bytes(), original[name])


if __name__ == '__main__':
    unittest.main()
