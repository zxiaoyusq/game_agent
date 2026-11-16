import copy, importlib.util, json, unittest
from pathlib import Path

root=Path.cwd()
spec=importlib.util.spec_from_file_location('oc_compile',root/'tools/compile_levels.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class ExpandedGravityDirections(unittest.TestCase):
 def test_8x10_supports_up_and_right(self):
  source=json.loads((root/'baseline/data.js').read_text(encoding='utf8'))
  cfg=json.loads((root/'tests/fixtures/level17-left-candidate.json').read_text(encoding='utf8'))
  for direction in ('gravity_up','gravity_right'):
   candidate=copy.deepcopy(cfg);candidate['levels'][0]['movement']=direction
   module.compile_data(source,candidate)

if __name__=='__main__':unittest.main()
