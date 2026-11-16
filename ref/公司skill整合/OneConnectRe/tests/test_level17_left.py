import importlib.util,json,unittest
from pathlib import Path
root=Path.cwd();spec=importlib.util.spec_from_file_location('oc_compile',root/'tools/compile_levels.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ExpandedLeft(unittest.TestCase):
 def test_expanded_left_and_invalid_direction(self):
  src=json.loads((root/'baseline/data.js').read_text(encoding='utf8'));cfg=json.loads((root/'tests/fixtures/level17-left-candidate.json').read_text(encoding='utf8'));m.compile_data(src,cfg)
  cfg['levels'][0]['movement']='gravity_diagonal'
  with self.assertRaises(ValueError):m.compile_data(src,cfg)
if __name__=='__main__':unittest.main()
