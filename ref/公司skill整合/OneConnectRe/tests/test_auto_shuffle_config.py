import importlib.util,json,unittest
from pathlib import Path
class AutoShuffleConfig(unittest.TestCase):
 def test_policy_is_optional_and_validated(self):
  spec=importlib.util.spec_from_file_location('levels',Path('tools/compile_levels.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);src=json.loads(Path('baseline/data.js').read_text(encoding='utf8'));m.compile_data(src,{'levels':[{'level':2,'seconds':180,'autoShuffle':'free'}]})
  for value in ('paid','',False,None):
   with self.assertRaises(ValueError):m.compile_data(src,{'levels':[{'level':2,'seconds':180,'autoShuffle':value}]})
