import importlib.util
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

root = Path.cwd()
spec = importlib.util.spec_from_file_location('package', root / 'tools/build_game_package.py')
import sys
sys.path.insert(0, str(root / 'tools'))
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)

class CandidatePackage(unittest.TestCase):
    def test_pixel_identical_effects_may_be_packaged_in_disposable_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            game = Path(tmp) / 'game'
            shutil.copytree(root / 'analysis/ui_iteration_candidate_v230_rc4/game', game)
            out = Path(tmp) / 'game.zip'
            count, size, digest = package.create(game, out, allow_lossless_effect_reencoding=True)
            self.assertGreater(count, 0)
            self.assertGreater(size, 0)
            self.assertEqual(len(digest), 64)
            with zipfile.ZipFile(out) as archive:
                self.assertIsNone(archive.testzip())
                self.assertEqual(archive.read('images/dots-sheet0.png'), (game / 'images/dots-sheet0.png').read_bytes())

    def test_changed_effect_pixels_are_rejected(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as tmp:
            game = Path(tmp) / 'game'
            shutil.copytree(root / 'analysis/ui_iteration_candidate_v230_rc4/game', game)
            effect = game / 'images/dots-sheet0.png'
            with Image.open(effect) as image:
                altered = image.convert('RGBA')
            pixel = altered.getpixel((0, 0))
            altered.putpixel((0, 0), (pixel[0] ^ 255, pixel[1], pixel[2], pixel[3]))
            altered.save(effect)
            with self.assertRaisesRegex(ValueError, 'effect pixel mismatch'):
                package.create(game, Path(tmp) / 'game.zip', allow_lossless_effect_reencoding=True)

if __name__ == '__main__':
    unittest.main()
