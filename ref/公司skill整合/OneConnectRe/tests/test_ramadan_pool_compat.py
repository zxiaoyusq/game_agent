from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'tools'))
from prepare_gameplay_layout_candidate import validate_candidate_pool


class PoolCompatibility(unittest.TestCase):
    def test_original_themes_keep_30_and_ramadan_caps_20(self):
        base={'generator':{'typeCount':2},'theme':0}
        validate_candidate_pool([21,30],base,[30,30,30,20])
        validate_candidate_pool([1,20],dict(base,theme=3),[30,30,30,20])
        with self.assertRaises(ValueError): validate_candidate_pool([1,21],dict(base,theme=3),[30,30,30,20])
        with self.assertRaises(ValueError): validate_candidate_pool([1,1],base,[30,30,30])


if __name__=='__main__': unittest.main()
