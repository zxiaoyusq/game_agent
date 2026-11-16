import copy,importlib.util,json,unittest
from pathlib import Path
root=Path.cwd();spec=importlib.util.spec_from_file_location('compiler',root/'tools/compile_levels.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ExpandedStatic(unittest.TestCase):
 def test_8x12_static_and_gravity_requires_bounds(self):
  src=json.loads((root/'baseline/data.js').read_text(encoding='utf8'));cfg=json.loads((root/'tests/fixtures/level16-safe-layout-candidate.json').read_text(encoding='utf8'));m.compile_data(src,cfg)
  for movement in ['gravity_up','gravity_down','gravity_left','gravity_right']:
   x=copy.deepcopy(cfg);x['levels'][0]['movement']=movement
   with self.assertRaises(ValueError):m.compile_data(src,x)
  old=copy.deepcopy(cfg);old['levels'][0]['boardSize'].update(itemSize=75,offsetX=160,offsetY=35)
  with self.assertRaises(ValueError):m.compile_data(src,old)
if __name__=='__main__':unittest.main()
