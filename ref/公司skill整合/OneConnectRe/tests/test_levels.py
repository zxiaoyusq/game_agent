import importlib.util, json, unittest
from pathlib import Path
p=Path('tools/compile_levels.py')
class Levels(unittest.TestCase):
 def test_config_generates_specific_timers_and_preserves_fallback(self):
  self.assertTrue(p.exists(),'level compiler is missing')
  spec=importlib.util.spec_from_file_location('levels',p);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
  source=json.loads(Path('baseline/data.js').read_text(encoding='utf8')); data=mod.compile_data(source,{'levels':[{'level':1,'seconds':180},{'level':2,'seconds':120},{'level':101,'seconds':240}]})
  sheet=next(x for x in data['project'][6] if x[0]=='menuEvent'); self.assertEqual(next(x for x in sheet[1] if len(x)>3 and x[0]==1 and x[1]=='timerInit')[3],180)
  game=next(x for x in data['project'][6] if x[0]=='gameEvent'); event=game[1][11][7][3]; self.assertIn([11,'timer'],event[6][4][5]); self.assertTrue(any('101' in json.dumps(x) and '240' in json.dumps(x) for x in event[7]))
 def test_board_validated(self):
  self.assertTrue(p.exists());spec=importlib.util.spec_from_file_location('levels',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  source=json.loads(Path('baseline/data.js').read_text(encoding='utf8'));board=[[x//2+1 for x in range(12)] for y in range(6)]
  m.compile_data(source,{'levels':[{'level':2,'seconds':120,'board':board}]})
  board[0][0]=20
  with self.assertRaises(ValueError):m.compile_data(source,{'levels':[{'level':2,'seconds':120,'board':board}]})
 def test_invalid_duplicate_rejected(self):
  self.assertTrue(p.exists(),'level compiler is missing');spec=importlib.util.spec_from_file_location('levels',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  source=json.loads(Path('baseline/data.js').read_text(encoding='utf8'))
  with self.assertRaises(ValueError):m.compile_data(source,{'levels':[{'level':2,'seconds':60},{'level':2,'seconds':70}]})
if __name__=='__main__':unittest.main()
