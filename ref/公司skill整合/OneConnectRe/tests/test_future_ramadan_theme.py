import json
import os
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent.parent


def read_config(path):
    text = path.read_text(encoding='utf8').strip()
    prefix = 'window.oneConnectLevels='
    if not text.startswith(prefix) or not text.endswith(';'):
        raise ValueError('invalid level configuration')
    return json.loads(text[len(prefix):-1])


class FutureRamadanTheme(unittest.TestCase):
    def test_override_only_changes_theme_on_compatible_level(self):
        game = Path(os.environ['ONECONNECT_CANDIDATE'])
        candidate = read_config(game / 'level-config.js')
        original = read_config(ROOT / 'game/level-config.js')
        overrides = json.loads((ROOT / 'config/theme_overrides_candidate.json').read_text(encoding='utf8'))
        for row in candidate['levels']:
            level = str(row['level'])
            old = next(x for x in original['levels'] if x['level'] == row['level'])
            if level in overrides:
                self.assertEqual(overrides[level], 3)
                self.assertLessEqual(row['generator']['typeCount'], 20)
            self.assertEqual(row, old)
        data = json.loads((game / 'data.js').read_text(encoding='utf8'))
        theme = next(a for a in data['project'][3][5][7] if a[0] == 't3')
        self.assertEqual(len(theme[7]), 20)
        board_hooks = (game / 'board-hooks.js').read_text(encoding='utf8')
        self.assertIn('var projectThemeOverrides=' + json.dumps(overrides, separators=(',', ':')), board_hooks)
        self.assertIn('if (theme && !candidateSavedThemeActive)', board_hooks)


if __name__ == '__main__':
    unittest.main()
