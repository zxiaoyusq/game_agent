from pathlib import Path
import importlib.util,json,tempfile,unittest
root=Path.cwd();compiler=root/'analysis/tile_capacity_candidate/tools/compile_levels.py'
class CapacityCompile(unittest.TestCase):
 def test_fixed_and_generated_and_reject_31(self):
  spec=importlib.util.spec_from_file_location('candidate_compile',compiler);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  source=json.loads((root/'baseline/data.js').read_text(encoding='utf8'));board=[[0]*12 for _ in range(6)];board[0][0]=board[0][1]=30
  m.compile_data(source,{'levels':[{'level':13,'seconds':180,'board':board}]})
  m.compile_data(source,{'levels':[{'level':13,'seconds':180,'movement':'static','generator':{'mask':[[1]*12 for _ in range(6)],'typeCount':30}}]})
  board[0][0]=board[0][1]=31
  with self.assertRaises(ValueError):m.compile_data(source,{'levels':[{'level':13,'seconds':180,'board':board}]})
if __name__=='__main__':unittest.main()
