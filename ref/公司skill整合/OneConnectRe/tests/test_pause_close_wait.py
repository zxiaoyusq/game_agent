import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
spec = importlib.util.spec_from_file_location('candidate_builder', ROOT / 'tools' / 'prepare_gameplay_layout_candidate.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class PauseWaitTest(unittest.TestCase):
    def test_path_mask_scope_excludes_movement_and_generation(self):
        data = json.loads((ROOT / 'game' / 'data.js').read_text(encoding='utf8'))
        ids = builder.native_path_event_sids(data)
        self.assertIn(387012710271463, ids)
        self.assertIn(989105087692895, ids)
        self.assertNotIn(941164143105040, ids)
        self.assertNotIn(870165811963617, ids)
        self.assertNotIn(291933957018453, ids)

    def test_wait_is_immediately_before_pause_hide(self):
        data = json.loads((ROOT / 'game' / 'data.js').read_text(encoding='utf8'))
        runtime = (ROOT / 'game' / 'c2runtime.js').read_text(encoding='utf8')
        builder.add_pause_close_wait(data, runtime)
        result = []
        tutorial = []
        def visit(v):
            if isinstance(v, list):
                if len(v) > 6 and v[4] == 854484185937641: result.append(v[6])
                if len(v) > 6 and v[4] == 462235957291603: tutorial.append(v[6])
                for x in v: visit(x)
            elif isinstance(v, dict):
                for x in v.values(): visit(x)
        visit(data)
        actions = result[0]
        index = next(i for i, a in enumerate(actions) if a[3] == 918927348401778)
        self.assertEqual(actions[index-1], [-1, 85, None, 874223100987651, False, [[0, [1, .18]]]])
        actions = tutorial[0]
        index = next(i for i, a in enumerate(actions) if a[3] == 268127763738893)
        self.assertEqual(actions[index-1], [-1, 85, None, 874223100987652, False, [[0, [1, .18]]]])


if __name__ == '__main__': unittest.main()
