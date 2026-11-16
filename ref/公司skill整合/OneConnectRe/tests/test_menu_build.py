import importlib.util,json,unittest
from pathlib import Path
class MenuBuild(unittest.TestCase):
 def test_play_starts_level_without_theme_picker(self):
  spec=importlib.util.spec_from_file_location('levels',Path('tools/compile_levels.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  source=json.loads(Path('baseline/data.js').read_text(encoding='utf8'));d=m.compile_data(source,{'levels':[]});s=next(x for x in d['project'][6] if x[0]=='menuEvent');a=s[1][18][7][0][6]
  self.assertFalse(any(x[0]==-1 and x[1]==84 and x[5]==[[5,[2,'Theme']],[3,1]] for x in a))
  self.assertTrue(any(x[0]==-1 and x[5]==[[11,'theme'],[7,[0,0]]] for x in a))
  self.assertTrue(any(x[0]==13 and x[1]==178 for x in a))
 def test_unexpected_menu_fails_without_mutating_original(self):
  spec=importlib.util.spec_from_file_location('levels',Path('tools/compile_levels.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  src=json.loads(Path('baseline/data.js').read_text(encoding='utf8'));sheet=next(x for x in src['project'][6] if x[0]=='menuEvent');sheet[1][18][7][0][6][3][3]=1
  with self.assertRaises(ValueError):m.compile_data(src,{'levels':[]})
