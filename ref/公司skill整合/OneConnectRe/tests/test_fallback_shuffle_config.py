import importlib.util,json,unittest
from pathlib import Path
root=Path.cwd();spec=importlib.util.spec_from_file_location('oc_compile',root/'tools/compile_levels.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class FallbackShuffleConfig(unittest.TestCase):
 def test_explicit_fallback_and_level_override(self):
  source=json.loads((root/'baseline/data.js').read_text(encoding='utf8'))
  m.compile_data(source,{'fallbackAutoShuffle':'free','levels':[{'level':13,'seconds':180,'autoShuffle':'original'}]})
 def test_invalid_fallback_rejected(self):
  source=json.loads((root/'baseline/data.js').read_text(encoding='utf8'))
  for value in ('bad','original',True,None):
   with self.subTest(value=value),self.assertRaises(ValueError):m.compile_data(source,{'fallbackAutoShuffle':value,'levels':[{'level':13,'seconds':180}]})
if __name__=='__main__':unittest.main()
