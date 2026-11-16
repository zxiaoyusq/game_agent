import importlib.util,json,unittest
from pathlib import Path
class ThemeConfig(unittest.TestCase):
 def test_theme_range(self):
  spec=importlib.util.spec_from_file_location('levels',Path('tools/compile_levels.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);src=json.loads(Path('baseline/data.js').read_text(encoding='utf8'))
  for value in (0,1,2):m.compile_data(src,{'levels':[{'level':1,'seconds':300,'theme':value}]})
  board=[[0]*12 for _ in range(6)];board[0][0]=board[0][1]=20
  m.compile_data(src,{'levels':[{'level':1,'seconds':300,'theme':3,'board':board}]})
  board[0][0]=board[0][1]=21
  with self.assertRaises(ValueError):m.compile_data(src,{'levels':[{'level':1,'seconds':300,'theme':3,'board':board}]})
  for value in (-1,4,True,'1'):
   with self.assertRaises(ValueError):m.compile_data(src,{'levels':[{'level':1,'seconds':300,'theme':value}]})
